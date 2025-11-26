from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from .models import Profile, AgricultureProgram, Registration, Candidate, University, Notification
from .models import ActivityLog
import logging
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm,
    ProgramRegistrationForm, AdminRegistrationForm,
    CandidateForm, CandidateSearchForm, ProgramSearchForm,
    ComprehensiveRegisterForm
)
from .forms_email import CustomPasswordResetForm
import csv
import xlsxwriter
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import uuid
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
import os
import json
from .decorators import ajax_login_required

# Initialize logger
logger = logging.getLogger(__name__)

@login_required
def cancel_application(request, candidate_id):
    """Cancel a candidate's application to a program and restore program capacity."""
    # Get candidate record ensuring it belongs to the current user
    candidate = get_object_or_404(
        Candidate.objects.filter(
            Q(created_by=request.user) | Q(email=request.user.email),
            id=candidate_id
        )
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get program for notification before deletion
                program = candidate.program
                program_title = program.title if program else 'Unknown Program'
                
                # Increment program capacity if program exists
                if program:
                    AgricultureProgram.objects.filter(id=program.id).update(capacity=F('capacity') + 1)
                
                # Delete the candidate application
                candidate.delete()
                
                # Create a notification for the user
                Notification.add_notification(
                    user=request.user,
                    message=f"Your application for {program_title} has been cancelled successfully.",
                    notification_type=Notification.INFO,
                )
                
                messages.success(request, f'Your application for {program_title} has been cancelled successfully.')
                
                # Clear related cache entries
                try:
                    cache_keys = [
                        'candidate_list:all',
                        f'candidate_detail:{candidate_id}',
                    ]
                    if program:
                        cache_keys.extend([
                            f'program_candidates:{program.id}',
                            f'program_detail:{program.id}',
                            f'program_stats:{program.id}'
                        ])
                    
                    for key in cache_keys:
                        try:
                            cache.delete(key)
                        except Exception as e:
                            logger.warning(f"Cache clear failed for key {key}: {e}")
                except Exception as e:
                    logger.warning(f"Cache operations failed: {e}")
                    # Continue even if cache fails
                
                return redirect('program_list')
                
        except Exception as e:
            logger.error(f"Error cancelling application: {e}")
            messages.error(request, 'An error occurred while cancelling your application. Please try again.')
            return redirect('profile')
    
    return render(request, 'cancel_application.html', {'candidate': candidate})


@require_GET
def health_check(request):
    """
    Health check endpoint for monitoring and SLO tracking
    Returns 200 if all systems are operational
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
        
        # Check critical models can be queried
        user_count = User.objects.count()
        program_count = AgricultureProgram.objects.count()
        
        # Check cache connectivity
        cache_status = "healthy"
        try:
            cache.set('health_check', 'ok', timeout=60)
            if cache.get('health_check') != 'ok':
                cache_status = "unhealthy"
        except Exception:
            cache_status = "unhealthy"
        
        health_data = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "checks": {
                "database": db_status,
                "cache": cache_status,
                "users": user_count,
                "programs": program_count,
            },
            "performance": {
                "cache_backend": settings.CACHES['default']['BACKEND'],
                "session_engine": settings.SESSION_ENGINE,
            },
            "version": "2.0"
        }
        
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        error_data = {
            "status": "unhealthy",
            "timestamp": timezone.now().isoformat(),
            "error": str(e),
            "version": "2.0"
        }
        
        return JsonResponse(error_data, status=503)


def index(request):
    """Home page view - shows different pages for guests vs authenticated users"""
    # Check for auto_open_modal query parameter
    auto_open_modal = request.GET.get('auto_open_modal', '')

    # If user is not authenticated, show guest landing page
    if not request.user.is_authenticated:
        return render(request, 'guest_landing.html', {'auto_open_modal': auto_open_modal})

    # For authenticated users, show the main programs landing page
    # Get featured programs first, then regular programs if needed
    featured_programs = AgricultureProgram.objects.filter(is_featured=True).order_by('-start_date')[:6]
    if featured_programs.count() < 3:
        # If less than 3 featured programs, show latest programs
        programs = AgricultureProgram.objects.all().order_by('-start_date')[:6]
    else:
        programs = featured_programs
    return render(request, 'index.html', {'programs': programs, 'auto_open_modal': auto_open_modal})


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
def register(request):
    """Comprehensive user registration view with extended profile fields and OAuth support"""
    from .oauth_utils import (
        get_oauth_session_data, clear_oauth_session_data,
        ProfilePictureDownloader
    )
    import secrets
    
    # Check for OAuth data in session
    oauth_data = get_oauth_session_data(request)
    
    if request.method == 'POST':
        form = ComprehensiveRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check if a user with this username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f'An account with username "{username}" already exists. Please choose a different username.')
                return render(request, 'register.html', {'form': form, 'oauth_data': oauth_data})

            if User.objects.filter(email=email).exists():
                messages.error(request, f'An account with email "{email}" already exists. Please use a different email or try to log in.')
                return render(request, 'register.html', {'form': form, 'oauth_data': oauth_data})

            # Save user and profile
            user = form.save()
            profile = form.save_profile(user)

            # Handle OAuth-specific data
            if oauth_data:
                # Save OAuth provider information
                profile.oauth_provider = oauth_data.get('provider')
                profile.oauth_id = oauth_data.get('oauth_id')
                
                # Email is verified if it came from OAuth
                profile.email_verified = oauth_data.get('email_verified', True)
                
                # Generate random password for OAuth users (they won't use it)
                if oauth_data.get('provider') != 'email':
                    random_password = secrets.token_urlsafe(32)
                    user.set_password(random_password)
                    user.save()
                
                profile.save()
                
                # Download and save profile picture if available
                picture_url = oauth_data.get('picture')
                if picture_url:
                    ProfilePictureDownloader.download_and_save_picture(
                        profile,
                        picture_url,
                        oauth_data.get('provider', 'oauth')
                    )
                
                # Clear OAuth data from session
                clear_oauth_session_data(request)
            else:
                # Mark email as verified for email signup too
                profile.email_verified = True
                profile.save()

            # Create welcome notification
            Notification.add_notification(
                user=user,
                message="Welcome to AgroStudies! Your comprehensive profile has been created successfully.",
                notification_type=Notification.SUCCESS,
                link="/profile/"
            )

            messages.success(request, f'Account created for {username}! Your profile is now complete. You can log in.')
            # Redirect to index page with modal auto-open instead of login page
            return redirect('/?auto_open_modal=login')
    else:
        # Pre-fill form with OAuth data if available
        form = ComprehensiveRegisterForm()
        if oauth_data:
            # Pre-populate form fields
            initial_data = {
                'email': oauth_data.get('email'),
                'confirm_email': oauth_data.get('email'),
                'first_name': oauth_data.get('first_name'),
                'last_name': oauth_data.get('last_name'),
            }
            form = ComprehensiveRegisterForm(initial=initial_data)
    
    # Clear the auto-open flag after we've retrieved the OAuth data
    if 'auto_open_register_modal' in request.session:
        del request.session['auto_open_register_modal']
        request.session.modified = True
    
    context = {
        'form': form,
        'oauth_data': oauth_data,
    }
    return render(request, 'register.html', context)


@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def comprehensive_register(request):
    """Comprehensive user registration view with extended profile fields"""
    if request.method == 'POST':
        form = ComprehensiveRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check if a user with this username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f'An account with username "{username}" already exists. Please choose a different username.')
                return render(request, 'comprehensive_register.html', {'form': form})

            if User.objects.filter(email=email).exists():
                messages.error(request, f'An account with email "{email}" already exists. Please use a different email or try to log in.')
                return render(request, 'comprehensive_register.html', {'form': form})

            # Save user and profile
            user = form.save()
            profile = form.save_profile(user)

            # Mark email as verified (no email verification in this flow)
            profile.email_verified = True
            profile.save()

            # Create welcome notification
            Notification.add_notification(
                user=user,
                message="Welcome to AgroStudies! Your comprehensive profile has been created successfully.",
                notification_type=Notification.SUCCESS,
                link="/profile/"
            )

            messages.success(request, f'Account created for {username}! Your profile is now complete.')
            return redirect('profile')
    else:
        form = ComprehensiveRegisterForm()
    return render(request, 'comprehensive_register.html', {'form': form})


def verify_email(request, token):
    """Email verification view"""
    try:
        profile = Profile.objects.get(verification_token=token)
        # Check if token is valid (not expired)
        if profile:
            profile.email_verified = True
            profile.verification_token = None
            profile.save()
            
            messages.success(request, 'Your email has been verified successfully! You can now log in.')
            return render(request, 'email_verification.html', {'success': True})
    except Profile.DoesNotExist:
        error_message = 'Invalid verification link. It may have expired or already been used.'
        
    return render(request, 'email_verification.html', {
        'success': False,
        'error_message': error_message if 'error_message' in locals() else 'Verification failed.'
    })


def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = Profile.objects.get(user=user)
            
            if profile.email_verified:
                messages.info(request, 'This email is already verified. You can log in now.')
                return redirect('login')
            
            # Generate new token
            token = str(uuid.uuid4())
            profile.verification_token = token
            profile.save()
            
            # Send verification email
            current_site = get_current_site(request)
            mail_subject = 'Activate your AgroStudies account'
            message = render_to_string('verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'https' if request.is_secure() else 'http',
                'token': token,
            })
            send_mail(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return render(request, 'email_verification_sent.html', {'email': user.email})
        except (User.DoesNotExist, Profile.DoesNotExist):
            messages.error(request, 'No user found with this email address.')
    
    return render(request, 'resend_verification.html')


@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def admin_register(request):
    """Admin registration view"""
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile auto-created by signal, no need to create manually
            username = form.cleaned_data.get('username')
            messages.success(request, f'Admin account created for {username}! You can now log in.')
            # Redirect to index page with modal auto-open instead of login page
            return redirect('/?auto_open_modal=login')
    else:
        form = AdminRegistrationForm()
    return render(request, 'admin_register.html', {'form': form})


@ratelimit(key='ip', rate='5/5m', method='POST', block=True)
def login_view(request):
    """Login view without email verification check"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Create profile if it doesn't exist (for backward compatibility)
                try:
                    profile = Profile.objects.get(user=user)
                except Profile.DoesNotExist:
                    Profile.objects.create(user=user, email_verified=True)
                
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('index')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')


def auth_required(request):
    """Guest-friendly prompt shown when unauthenticated users hit a protected page.
    Renders the home page with a message and auto-opens the login/register modal.
    """
    if request.user.is_authenticated:
        return redirect('profile')

    messages.info(request, 'Please log in or create an account to continue.')
    # Reuse index page and signal the base template to open the login modal automatically
    programs = AgricultureProgram.objects.all().order_by('-start_date')[:5]
    return render(request, 'index.html', { 'programs': programs, 'auto_open_modal': 'login' })


@login_required
def profile(request):
    """User profile view"""
    form_with_errors = False
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            # Check if user wants to delete the profile image
            if 'delete_image' in request.POST and request.user.profile.profile_image:
                # Save the path to delete the file after saving the form
                old_image = request.user.profile.profile_image.path
                request.user.profile.profile_image = None
                
                # Delete the file if it exists
                if os.path.exists(old_image):
                    os.remove(old_image)
            
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')

            # Sync updated identity fields to any of the user's candidate applications
            try:
                candidate_qs = Candidate.objects.filter(Q(created_by=request.user) | Q(email=request.user.email))
                if candidate_qs.exists():
                    candidate_qs.update(
                        first_name=request.user.first_name,
                        last_name=request.user.last_name,
                        email=request.user.email,
                        father_name=request.user.profile.father_name,
                        mother_name=request.user.profile.mother_name,
                        date_of_birth=request.user.profile.date_of_birth,
                        gender=request.user.profile.gender,
                        country_of_birth=request.user.profile.country_of_birth,
                        nationality=request.user.profile.nationality,
                        religion=request.user.profile.religion,
                    )
            except Exception as e:
                # Best-effort sync; do not block profile save on errors
                logger.exception(f"Failed to sync candidate data for user {request.user.id}: {e}")
                pass

            # Create a notification
            Notification.add_notification(
                request.user,
                "Your profile has been successfully updated.",
                Notification.SUCCESS
            )
            
            return redirect('profile')
        else:
            form_with_errors = True
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Get user registrations and any candidate applications (direct apply flow)
    registrations = Registration.objects.filter(user=request.user).order_by('-registration_date')
    candidate_apps = Candidate.objects.filter(Q(created_by=request.user) | Q(email=request.user.email)).order_by('-created_at')
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'registrations': registrations,
        'candidate_apps': candidate_apps,
        'form_with_errors': form_with_errors
    }
    return render(request, 'profile.html', context)


@login_required
@require_POST
def clear_all_documents(request):
    """Clear all required documents from user's profile"""
    try:
        profile = request.user.profile
        
        # List of document fields to clear
        document_fields = [
            'tor', 'nc2_tesda', 'diploma', 'good_moral', 
            'nbi_clearance', 'passport_scan', 'academic_certificate'
        ]
        
        # Delete files and clear fields
        for field_name in document_fields:
            file_field = getattr(profile, field_name, None)
            if file_field:
                # Delete the physical file if it exists
                try:
                    if file_field.name and os.path.exists(file_field.path):
                        os.remove(file_field.path)
                except Exception as e:
                    logger.warning(f"Could not delete file {field_name}: {str(e)}")
                
                # Clear the field
                setattr(profile, field_name, None)
        
        # Save the profile
        profile.save()
        
        # Deactivate all file records in UploadedFile tracking system
        from core.models import UploadedFile
        UploadedFile.objects.filter(
            user=request.user,
            document_type__in=document_fields,
            is_active=True
        ).update(is_active=False)
        
        messages.success(request, 'All required documents have been cleared successfully.')
        
        # Create a notification
        Notification.add_notification(
            request.user,
            "All required documents have been cleared from your profile.",
            Notification.INFO
        )
        
    except Exception as e:
        logger.exception(f"Error clearing documents for user {request.user.id}: {str(e)}")
        messages.error(request, 'An error occurred while clearing documents. Please try again.')
    
    return redirect('profile')


def program_list(request):
    """List all available programs"""
    # Try to get from cache first, but only if no filters are applied
    cache_key = 'programs_list:all'
    programs = None
    
    if not request.GET:  # Only use cache for unfiltered list
        try:
            programs = cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for programs list: {e}")
    
    if programs is None:
        programs = AgricultureProgram.objects.select_related().all().order_by('-start_date')
        if not request.GET:  # Cache only unfiltered results
            try:
                cache.set(cache_key, programs, timeout=300)  # Cache for 5 minutes
            except Exception as e:
                logger.warning(f"Cache set failed for programs list: {e}")
    
    form = ProgramSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        location = form.cleaned_data.get('location')
        country = form.cleaned_data.get('country')
        gender = form.cleaned_data.get('gender')

        if query:
            programs = programs.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        if location:
            programs = programs.filter(location__icontains=location)
            
        if country:
            programs = programs.filter(country__icontains=country)
        
        if gender:
            programs = programs.filter(required_gender=gender)
            
        # Filter out programs with expired registration deadlines
        programs = programs.filter(
            Q(registration_deadline__isnull=True) |  # No deadline set
            Q(registration_deadline__gte=timezone.now().date())  # Or deadline not passed
        )

    # Pagination
    paginator = Paginator(programs, 10)  # Show 10 programs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Track if the user has already applied to ANY program (one-time application rule)
    applied_program_ids = set()
    has_applied_any = False
    if request.user.is_authenticated and not request.user.is_staff:
        reg_qs = Registration.objects.filter(user=request.user)
        cand_qs = Candidate.objects.filter(Q(created_by=request.user) | Q(email=request.user.email))
        has_applied_any = reg_qs.exists() or cand_qs.exists()
        if reg_qs.exists():
            applied_program_ids.update(reg_qs.values_list('program_id', flat=True))
        if cand_qs.exists():
            applied_program_ids.update([pid for pid in cand_qs.values_list('program_id', flat=True) if pid is not None])
    
    context = {
        'page_obj': page_obj,
        'applied_program_ids': applied_program_ids,
        'has_applied_any': has_applied_any,
        'form': form,
    }
    
    # Don't cache the full context - paginator objects can't be pickled
    # Note: Caching disabled here to avoid pickling errors with Django objects
    return render(request, 'program_list.html', context)


def program_detail(request, program_id):
    """Show details of a specific program"""
    program = get_object_or_404(AgricultureProgram.objects.select_related(), id=program_id)
    
    # Check if user is already applied/registered (Registration or Candidate)
    user_registered = False
    registration = None
    has_applied_any = False
    if request.user.is_authenticated:
        try:
            registration = Registration.objects.get(user=request.user, program=program)
            user_registered = True
        except Registration.DoesNotExist:
            # Also consider an existing Candidate as applied
            if Candidate.objects.filter(program=program).filter(
                Q(created_by=request.user) | Q(email=request.user.email)
            ).exists():
                user_registered = True
        # One-time application rule across all programs
        has_applied_any = Registration.objects.filter(user=request.user).exists() or \
            Candidate.objects.filter(Q(created_by=request.user) | Q(email=request.user.email)).exists()
    
    return render(request, 'program_detail.html', {
        'program': program,
        'user_registered': user_registered,
        'registration': registration,
        'has_applied_any': has_applied_any,
    })


@ajax_login_required
def program_register(request, program_id):
    """Legacy route: redirect to new single-step candidate apply flow"""
    return redirect('candidate_apply', program_id=program_id)


@ajax_login_required
def apply_candidate(request, program_id):
    """Applicant-facing: simplified confirmation flow that uses profile data."""
    program = get_object_or_404(AgricultureProgram, id=program_id)
    
    # Check if registration is still open
    if not program.is_registration_open():
        messages.error(request, 'Registration for this program has ended.')
        return redirect('program_detail', program_id=program_id)
    
    profile = request.user.profile
    
    # Collect missing fields as warnings (but don't block application)
    # Users can apply and complete their profile later
    missing_fields = []
    if not profile.passport_number:
        missing_fields.append('Passport Number')
    if not profile.date_of_birth:
        missing_fields.append('Date of Birth')
    if not profile.country_of_birth:
        missing_fields.append('Country of Birth')
    if not profile.nationality:
        missing_fields.append('Nationality')
    if not profile.gender:
        missing_fields.append('Sex')
    if not profile.university:
        missing_fields.append('University')
    if not profile.specialization:
        missing_fields.append('Specialization')
    if not profile.passport_issue_date:
        missing_fields.append('Passport Issue Date')
    if not profile.passport_expiry_date:
        missing_fields.append('Passport Expiry Date')
    
    # Note: We no longer block the application for missing fields
    # They will be shown as warnings in the confirmation page

    # New guard: Check program capacity
    if program.capacity <= 0:
        messages.error(request, 'This program has no available slots.', extra_tags='error')
        return redirect('program_detail', program_id=program.id)

    # New guard: Check program requirements
    if program.required_gender != 'Any' and profile.gender != program.required_gender:
        messages.error(request, f"This program requires applicants to be {program.required_gender}.", extra_tags='error')
        return redirect('program_detail', program_id=program.id)
    
    if program.requires_license and not profile.has_international_license:
        messages.error(request, "This program requires an international driver's license.", extra_tags='error')
        return redirect('program_detail', program_id=program.id)

    # Server-side guards
    # 1) Already applied to this program
    already_applied_this = Candidate.objects.filter(program=program).filter(
        Q(created_by=request.user) | Q(email=request.user.email)
    ).exists() or Registration.objects.filter(user=request.user, program=program).exists()
    if already_applied_this:
        messages.info(request, 'You have already applied to this program.')
        return redirect('program_detail', program_id=program.id)

    # 2) One-time application: if applied anywhere else, block
    has_applied_elsewhere = (
        Registration.objects.filter(user=request.user).exclude(program=program).exists() or
        Candidate.objects.filter(Q(created_by=request.user) | Q(email=request.user.email)).exclude(program=program).exists()
    )
    if has_applied_elsewhere:
        messages.warning(request, 'You have already applied to a different program and cannot submit another application.')
        return redirect('program_list')

    if request.method == 'POST':
        # User confirmed - create candidate from profile data
        try:
            with transaction.atomic():
                # Lock the program row for update to prevent concurrent capacity decrements
                program = AgricultureProgram.objects.select_for_update().get(id=program_id)
                
                # Re-check capacity inside transaction after acquiring lock
                if program.capacity <= 0:
                    messages.error(request, 'This program has no available slots.', extra_tags='error')
                    return redirect('program_detail', program_id=program.id)
                
                # Re-check if user already applied (inside transaction)
                already_applied_this = Candidate.objects.filter(program=program).filter(
                    Q(created_by=request.user) | Q(email=request.user.email)
                ).exists() or Registration.objects.filter(user=request.user, program=program).exists()
                if already_applied_this:
                    messages.info(request, 'You have already applied to this program.')
                    return redirect('program_detail', program_id=program.id)
                
                # Create candidate from profile data
                candidate = Candidate()
                candidate.created_by = request.user
                candidate.program = program
                candidate.status = Candidate.APPROVED
                
                # Copy data from profile (handle empty names gracefully)
                candidate.first_name = request.user.first_name or ''
                candidate.last_name = request.user.last_name or ''
                candidate.email = request.user.email or ''
                candidate.father_name = profile.father_name or ''
                candidate.mother_name = profile.mother_name or ''
                
                # These fields are validated before this point, so they should exist
                # But we handle None gracefully since model now allows blank/null
                candidate.date_of_birth = profile.date_of_birth
                candidate.gender = profile.gender or ''
                candidate.country_of_birth = profile.country_of_birth or ''
                candidate.nationality = profile.nationality or ''
                candidate.religion = profile.religion or ''
                
                # Passport details (validated fields)
                candidate.passport_number = profile.passport_number or ''
                candidate.passport_issue_date = profile.passport_issue_date
                candidate.passport_expiry_date = profile.passport_expiry_date
                
                # Education (validated fields)
                candidate.university = profile.university
                candidate.specialization = profile.specialization or ''
                candidate.secondary_specialization = profile.secondary_specialization or ''
                candidate.year_graduated = profile.graduation_year
                
                # Physical attributes
                candidate.shoes_size = profile.shoes_size or ''
                candidate.shirt_size = profile.shirt_size or ''
                candidate.smokes = profile.smokes or 'Never'
                
                # Documents - Copy ALL documents from profile to candidate
                if profile.profile_image:
                    candidate.profile_image = profile.profile_image
                if profile.license_scan:
                    candidate.license_scan = profile.license_scan
                if profile.passport_scan:
                    candidate.passport_scan = profile.passport_scan
                if profile.academic_certificate:
                    candidate.academic_certificate = profile.academic_certificate
                if profile.tor:
                    candidate.tor = profile.tor
                if profile.nc2_tesda:
                    candidate.nc2_tesda = profile.nc2_tesda
                if profile.diploma:
                    candidate.diploma = profile.diploma
                if profile.good_moral:
                    candidate.good_moral = profile.good_moral
                if profile.nbi_clearance:
                    candidate.nbi_clearance = profile.nbi_clearance
                
                # Save candidate
                candidate.save()
                
                # Atomically decrease program capacity
                AgricultureProgram.objects.filter(id=program.id).update(capacity=F('capacity') - 1)

                messages.success(request, f'Congratulations! Your application for {program.title} has been approved.')
                
                # Create a notification for the user
                Notification.add_notification(
                    user=request.user,
                    message=f"Congratulations! Your application for {program.title} has been approved. You're now ready to proceed with the next steps.",
                    notification_type=Notification.SUCCESS,
                    link=f"/candidates/{candidate.id}/"
                )
                
                # Clear related cache entries
                try:
                    cache_keys = [
                        'candidate_list:all',
                        f'program_candidates:{program_id}',
                        f'program_detail:{program_id}',
                        f'program_stats:{program_id}'
                    ]
                    for key in cache_keys:
                        try:
                            cache.delete(key)
                        except Exception as e:
                            logger.warning(f"Cache clear failed for key {key}: {e}")
                except Exception as e:
                    logger.warning(f"Cache operations failed: {e}")
                
                return redirect('profile')
                
        except Exception as e:
            # Enhanced error logging with full traceback and validation details
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error creating application for user {request.user.username} (ID: {request.user.id}), program {program_id}: {e}")
            logger.error(f"Traceback: {error_details}")
            
            # Try to extract validation error details if available
            if hasattr(e, 'message_dict'):
                logger.error(f"Validation errors: {e.message_dict}")
            
            # Show detailed error in development
            from django.conf import settings
            if settings.DEBUG:
                error_msg = f'Application Error: {str(e)}. Traceback: {error_details}'
                messages.error(request, error_msg)
            else:
                messages.error(
                    request, 
                    'An error occurred while processing your application. Our team has been notified. '
                    'Please ensure your profile information is complete and try again.'
                )
            return redirect('program_detail', program_id=program.id)
    
    # GET request - show confirmation page with profile data
    universities = University.objects.all().order_by('name')
    return render(request, 'program_apply_confirm.html', {
        'program': program,
        'profile': profile,
        'user': request.user,
        'missing_fields': missing_fields,
        'universities': universities,
    })


@login_required
def cancel_registration(request, registration_id):
    """Cancel a program registration"""
    registration = get_object_or_404(Registration, id=registration_id, user=request.user)
    
    if request.method == 'POST':
        program_title = registration.program.title
        registration.delete()
        messages.success(request, f'Your registration for {program_title} has been cancelled.')
        return redirect('profile')
    
    return render(request, 'cancel_registration.html', {'registration': registration})


@login_required
def candidate_list(request):
    """List candidates. Staff see all; applicants see only their own submission(s)."""
    if request.user.is_staff:
        candidates = Candidate.objects.select_related('university', 'program', 'created_by').all()
    else:
        # Show only the current user's candidate records
        candidates = Candidate.objects.select_related('university', 'program', 'created_by').filter(
            Q(created_by=request.user) | Q(email=request.user.email)
        )
    
    form = CandidateSearchForm(request.GET)
    
    # Apply filters (staff only)
    if form.is_valid() and request.user.is_staff:
        # Text search - search by name or email
        search = form.cleaned_data.get('search')
        if search:
            candidates = candidates.filter(
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) | 
                Q(email__icontains=search)
            )

        # Filter by country (country of birth)
        country = form.cleaned_data.get('country')
        if country:
            candidates = candidates.filter(country_of_birth=country)

        # Filter by nationality
        nationality = form.cleaned_data.get('nationality')
        if nationality:
            candidates = candidates.filter(nationality=nationality)

        # Filter by sex
        gender = form.cleaned_data.get('gender')
        if gender:
            candidates = candidates.filter(gender=gender)

        # Filter by specialization
        specialization = form.cleaned_data.get('specialization')
        if specialization:
            candidates = candidates.filter(specialization=specialization)

        # Filter by status
        status = form.cleaned_data.get('status')
        if status:
            candidates = candidates.filter(status=status)

        # Filter by date range - handle both old format (separate dates) and new format (date_range)
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        date_range = form.cleaned_data.get('date_range')

        # Handle new date_range format (takes priority over separate dates)
        if date_range and date_range.strip():
            # Parse the date range format "Aug 31 - Oct 24"
            try:
                import re
                date_match = re.match(r'(\w+\s+\d+) - (\w+\s+\d+)', date_range.strip())
                if date_match:
                    start_str, end_str = date_match.groups()
                    # Parse dates (assuming current year if not specified)
                    from datetime import datetime
                    current_year = datetime.now().year

                    # Try to parse with year first
                    try:
                        start_date_parsed = datetime.strptime(f"{start_str} {current_year}", "%b %d %Y")
                        end_date_parsed = datetime.strptime(f"{end_str} {current_year}", "%b %d %Y")
                    except ValueError:
                        # If parsing with current year fails, try with next year for end date
                        try:
                            start_date_parsed = datetime.strptime(f"{start_str} {current_year}", "%b %d %Y")
                            end_date_parsed = datetime.strptime(f"{end_str} {current_year + 1}", "%b %d %Y")
                        except ValueError:
                            # Fallback: assume same year
                            start_date_parsed = datetime.strptime(f"{start_str} {current_year}", "%b %d %Y")
                            end_date_parsed = datetime.strptime(f"{end_str} {current_year}", "%b %d %Y")

                    candidates = candidates.filter(created_at__date__gte=start_date_parsed.date())
                    candidates = candidates.filter(created_at__date__lte=end_date_parsed.date())
            except Exception as e:
                logger.warning(f"Error parsing date range '{date_range}': {e}")
                # Fall back to separate date fields if date_range parsing fails

        # Handle old format (separate start_date and end_date) - for backward compatibility
        if start_date and not date_range:
            candidates = candidates.filter(created_at__date__gte=start_date)
        if end_date and not date_range:
            from datetime import timedelta
            # Include the entire end date by adding one day and using less than
            end_date_next = end_date + timedelta(days=1)
            candidates = candidates.filter(created_at__date__lt=end_date_next)

        # Apply sorting
        sort_by = form.cleaned_data.get('sort_by')
        if sort_by:
            candidates = candidates.order_by(sort_by)
        else:
            candidates = candidates.order_by('-created_at')
    else:
        # Default sorting for non-staff users
        candidates = candidates.order_by('-created_at')
    
    # Check if export is requested
    export_format = request.GET.get('export')
    selected_candidates = request.GET.get('selected')
    
    if export_format:
        if selected_candidates:
            # Filter by selected candidate IDs
            selected_ids = [int(id) for id in selected_candidates.split(',')]
            export_queryset = candidates.filter(id__in=selected_ids)
        else:
            # Export all filtered candidates
            export_queryset = candidates
            
        if export_format == 'csv':
            return export_candidates_csv(request, export_queryset)
        elif export_format == 'excel':
            return export_candidates_excel(request, export_queryset)
        elif export_format == 'pdf':
            return export_candidates_pdf(request, export_queryset)
    
    # Pagination
    paginator = Paginator(candidates, 15)  # Show 15 candidates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'candidate_list.html', {
        'page_obj': page_obj,
        'form': form,
        'status_colors': {
            'Draft': 'secondary',
            'New': 'info',
            'Approved': 'success',
            'Rejected': 'danger'
        }
    })


@login_required
def export_candidates_csv(request, candidates=None):
    """Export candidates to CSV file with memory-efficient streaming"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.select_related('university', 'program').all().order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="candidates.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Passport Number', 'First Name', 'Last Name', 'Email', 'Date of Birth',
        'Gender', 'Nationality', 'University', 'Specialization', 'Status',
        'Program', 'Program Location', 'Date Added'
    ])
    
    # Use iterator() for memory efficiency with large datasets
    for candidate in candidates.iterator(chunk_size=100):
        writer.writerow([
            candidate.passport_number,
            candidate.first_name,
            candidate.last_name,
            candidate.email or '',
            candidate.date_of_birth.strftime('%Y-%m-%d'),
            candidate.gender,
            candidate.nationality,
            candidate.university.name,
            candidate.specialization,
            candidate.status,
            (candidate.program.title if candidate.program else ''),
            (candidate.program.location if candidate.program else ''),
            candidate.created_at.strftime('%Y-%m-%d')
        ])
    
    return response


@login_required
def export_candidates_excel(request, candidates=None):
    """Export candidates to Excel file with memory-efficient processing"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.select_related('university', 'program').all().order_by('-created_at')
    
    # Create an in-memory output file
    output = BytesIO()
    
    # Create a workbook and add a worksheet with remove_timezone option
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True, 'constant_memory': True})
    worksheet = workbook.add_worksheet()
    
    # Add a bold format to use to highlight cells
    bold = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    
    # Write some data headers
    headers = [
        'Passport Number', 'First Name', 'Last Name', 'Email', 'Date of Birth',
        'Gender', 'Nationality', 'Country of Birth', 'Religion', 'Father Name', 
        'Mother Name', 'University', 'Specialization', 'Secondary Specialization',
        'Smokes', 'Status', 'Program', 'Program Location', 'Date Added'
    ]
    
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, bold)
    
    # Start from the first cell below headers
    row = 1
    
    # Write data rows using iterator for memory efficiency
    for candidate in candidates.iterator(chunk_size=100):
        col = 0
        worksheet.write(row, col, candidate.passport_number); col += 1
        worksheet.write(row, col, candidate.first_name); col += 1
        worksheet.write(row, col, candidate.last_name); col += 1
        worksheet.write(row, col, candidate.email or ''); col += 1
        worksheet.write_datetime(row, col, candidate.date_of_birth, date_format); col += 1
        worksheet.write(row, col, candidate.gender); col += 1
        worksheet.write(row, col, candidate.nationality); col += 1
        worksheet.write(row, col, candidate.country_of_birth); col += 1
        worksheet.write(row, col, candidate.religion or ''); col += 1
        worksheet.write(row, col, candidate.father_name or ''); col += 1
        worksheet.write(row, col, candidate.mother_name or ''); col += 1
        worksheet.write(row, col, candidate.university.name); col += 1
        worksheet.write(row, col, candidate.specialization); col += 1
        worksheet.write(row, col, candidate.secondary_specialization or ''); col += 1
        worksheet.write(row, col, candidate.smokes); col += 1
        worksheet.write(row, col, candidate.status); col += 1
        # Program (farm) details
        worksheet.write(row, col, (candidate.program.title if candidate.program else '')); col += 1
        worksheet.write(row, col, (candidate.program.location if candidate.program else '')); col += 1
        worksheet.write_datetime(row, col, candidate.created_at, date_format); col += 1
        row += 1
    
    # Adjust column widths for better readability
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, len(header) + 2)
    
    # Close the workbook
    workbook.close()
    
    # Rewind the buffer
    output.seek(0)
    
    # Set up the HttpResponse
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=candidates.xlsx'
    
    return response


@login_required
def export_candidates_pdf(request, candidates=None):
    """Export candidates to PDF file with optimized queries"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.select_related('university', 'program').all().order_by('-created_at')
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Add title
    title = Paragraph("Candidates Report", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Styles for table content
    body_style = ParagraphStyle(name='BodySmall', fontSize=8, leading=10)
    header_style = ParagraphStyle(name='HeaderSmall', fontSize=9, leading=11)

    # Create data for table with wrapped cells
    headers = [
        'Passport Number', 'Name', 'Nationality', 'University',
        'Specialization', 'Status', 'Program', 'Program Location', 'Date Added'
    ]
    data = [[Paragraph(h, header_style) for h in headers]]

    for candidate in candidates:
        name = Paragraph(f"{candidate.first_name} {candidate.last_name}", body_style)
        university = Paragraph(candidate.university.name, body_style)
        specialization = Paragraph(candidate.specialization, body_style)
        program_title = Paragraph((candidate.program.title if candidate.program else ''), body_style)
        program_loc = Paragraph((candidate.program.location if candidate.program else ''), body_style)
        data.append([
            candidate.passport_number,
            name,
            candidate.nationality,
            university,
            specialization,
            candidate.status,
            program_title,
            program_loc,
            candidate.created_at.strftime('%Y-%m-%d')
        ])

    # Fit columns to available page width
    page_width, _ = landscape(letter)
    content_width = page_width - (30 + 30)
    weights = [75, 110, 70, 140, 120, 60, 120, 120, 70]
    scale = content_width / float(sum(weights))
    col_widths = [w * scale for w in weights]

    table = Table(data, colWidths=col_widths)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    # Apply alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(style)
    elements.append(table)
    
    # Build the document
    doc.build(elements)
    
    # Get the value of the buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="candidates.pdf"'
    response.write(pdf)
    
    return response


@login_required
def add_candidate(request):
    """Add a new candidate"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # Check if a username was provided (coming from the registrants page)
    username = request.GET.get('username')
    initial_data = {}
    registration_id = request.GET.get('registration_id')
    
    if username:
        try:
            user = User.objects.get(username=username)
            # Pre-fill form with user data if found
            initial_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'confirm_first_name': user.first_name,
                'confirm_surname': user.last_name
            }
            
            # Check for registrations by this user and pre-fill document fields
            registrations = Registration.objects.filter(user=user).order_by('-registration_date')
            if registrations.exists():
                # Initialize document fields as None
                documents = {
                    'tor': None,
                    'nc2_tesda': None,
                    'diploma': None,
                    'good_moral': None,
                    'nbi_clearance': None
                }
                
                # Check all registrations for documents
                for registration in registrations:
                    # For each document field, use the first non-empty value found
                    for doc_field in documents.keys():
                        if documents[doc_field] is None and getattr(registration, doc_field):
                            documents[doc_field] = getattr(registration, doc_field)
                
                # Add found documents to initial_data
                for doc_field, value in documents.items():
                    if value:
                        initial_data[doc_field] = value
                
                # Add a message to inform the admin that documents were pre-filled
                messages.info(request, f'Documents uploaded by {username} during program registration have been pre-filled.')
            
        except User.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        # Set created_by on form for duplicate file validation
        form.created_by = request.user
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.created_by = request.user
            candidate.status = 'Draft'  # Set initial status
            
            # If this candidate was created from a registration, associate with the program
            if registration_id:
                try:
                    registration = Registration.objects.get(id=registration_id)
                    # Associate the candidate with the program
                    candidate.program = registration.program
                    
                    # Mark registration as processed
                    registration.processed = True
                    registration.save()
                    
                    # Add a success message
                    messages.success(request, f'Registration for {registration.user.username} has been processed and removed from the registrants list.')
                except Registration.DoesNotExist:
                    pass
            
            candidate.save()
            
            messages.success(request, f'Candidate {candidate.first_name} {candidate.last_name} has been added successfully.')
            
            # Redirect back to the program registrants page if we came from there
            if registration_id:
                return redirect('program_registrants', program_id=registration.program.id)
            return redirect('candidate_list')
    else:
        form = CandidateForm(initial=initial_data)
    
    return render(request, 'candidate_form.html', {
        'form': form,
        'title': 'Add New Candidate',
        'button_text': 'Add Candidate',
        'registration_id': registration_id  # Pass this to the form so we can use it in POST
    })


@login_required
def edit_candidate(request, candidate_id):
    """Edit existing candidate"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # Force refresh from database to get latest file data
    candidate = get_object_or_404(Candidate.objects.select_related('created_by__profile'), id=candidate_id)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        # Set created_by on form for duplicate file validation
        form.created_by = candidate.created_by
        if form.is_valid():
            form.save()
            messages.success(request, f'Candidate {candidate.first_name} {candidate.last_name} has been updated successfully.')
            return redirect('candidate_list')
    else:
        form = CandidateForm(instance=candidate)
        # Set created_by on form for duplicate file validation
        form.created_by = candidate.created_by
    
    response = render(request, 'candidate_form.html', {
        'form': form,
        'candidate': candidate,
        'title': f'Edit Candidate: {candidate.first_name} {candidate.last_name}',
        'button_text': 'Update Candidate'
    })
    
    # Prevent browser caching to always show latest file data
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response


@login_required
def view_candidate(request, candidate_id):
    """View candidate details"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Status colors for the badge
    status_colors = {
        'Draft': 'secondary',
        'New': 'info',
        'Approved': 'success',
        'Rejected': 'danger'
    }

    return render(request, 'candidate_detail.html', {
        'candidate': candidate,
        'status_color': status_colors.get(candidate.status, 'secondary'),
    })


@login_required
def delete_candidate(request, candidate_id):
    """Delete a candidate"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        candidate_name = f"{candidate.first_name} {candidate.last_name}"
        program_id = candidate.program.id if candidate.program else None
        
        # Clear cache before deletion
        try:
            cache_keys = [
                'candidate_list:all',
                f'candidate_detail:{candidate_id}',
            ]
            if program_id:
                cache_keys.extend([
                    f'program_candidates:{program_id}',
                    f'program_detail:{program_id}',
                ])
            
            for key in cache_keys:
                try:
                    cache.delete(key)
                except Exception as e:
                    logger.warning(f"Cache clear failed for key {key}: {e}")
        except Exception as e:
            logger.warning(f"Cache operations failed during candidate deletion: {e}")
            # Continue with deletion even if cache fails
        
        candidate.delete()
        messages.success(request, f'Candidate {candidate_name} has been deleted successfully.')
        return redirect('candidate_list')
    
    return render(request, 'candidate_confirm_delete.html', {'candidate': candidate})



def help_page(request):
    """Registration help page"""
    return render(request, 'help.html')


def contact_page(request):
    """Contact page"""
    return render(request, 'contact.html')


@login_required
def program_registrants(request, program_id):
    """View registrants for a specific program"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    program = get_object_or_404(AgricultureProgram, id=program_id)
    # New logic: applicants go directly to Candidates. Show candidates for this program.
    candidates_qs = Candidate.objects.filter(program=program).order_by('-created_at')
    
    # Check if export is requested
    export_format = request.GET.get('export')
    if export_format:
        # Reuse candidates export with program-filtered queryset
        if export_format == 'csv':
            return export_candidates_csv(request, candidates_qs)
        elif export_format == 'excel':
            return export_candidates_excel(request, candidates_qs)
        elif export_format == 'pdf':
            return export_candidates_pdf(request, candidates_qs)
    
    # Pagination
    paginator = Paginator(candidates_qs, 20)  # Show 20 candidates per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'program_registrants.html', {
        'program': program,
        'page_obj': page_obj,
        'status_colors': {
            'Draft': 'secondary',
            'New': 'info',
            'Approved': 'success',
            'Rejected': 'danger'
        }
    })


@login_required
def export_registrants_csv(request, registrations=None, program=None):
    """Export program registrants to CSV"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If registrations not provided, get from program_id
    if registrations is None and program is None:
        program_id = request.GET.get('program_id')
        if not program_id:
            messages.error(request, 'Program ID is required.')
            return redirect('program_list')
        
        program = get_object_or_404(AgricultureProgram, id=program_id)
        registrations = Registration.objects.filter(program=program).order_by('-registration_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{program.title.replace(" ", "_")}_registrants.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'First Name', 'Last Name', 'Email', 
        'Registration Date', 'Status', 'Program', 'Program Location', 'Notes'
    ])
    
    for registration in registrations:
        writer.writerow([
            registration.user.username,
            registration.user.first_name,
            registration.user.last_name,
            registration.user.email,
            registration.registration_date.strftime('%Y-%m-%d'),
            registration.status,
            (registration.program.title if registration.program else (program.title if program else '')),
            (registration.program.location if registration.program else (program.location if program else '')),
            registration.notes
        ])
    
    return response


@login_required
def export_registrants_excel(request, registrations=None, program=None):
    """Export program registrants to Excel"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If registrations not provided, get from program_id
    if registrations is None and program is None:
        program_id = request.GET.get('program_id')
        if not program_id:
            messages.error(request, 'Program ID is required.')
            return redirect('program_list')
        
        program = get_object_or_404(AgricultureProgram, id=program_id)
        registrations = Registration.objects.filter(program=program).order_by('-registration_date')
    
    # Create an in-memory output file
    output = BytesIO()
    
    # Create a workbook and add a worksheet with remove_timezone option
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
    worksheet = workbook.add_worksheet()
    
    # Add formatting
    bold = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    
    # Write data headers
    headers = [
        'Username', 'First Name', 'Last Name', 'Email', 
        'Registration Date', 'Status', 'Program', 'Program Location', 'Notes'
    ]
    
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header, bold)
    
    # Start from the first cell below headers
    row = 1
    
    # Write data rows
    for registration in registrations:
        col = 0
        worksheet.write(row, col, registration.user.username); col += 1
        worksheet.write(row, col, registration.user.first_name); col += 1
        worksheet.write(row, col, registration.user.last_name); col += 1
        worksheet.write(row, col, registration.user.email); col += 1
        worksheet.write_datetime(row, col, registration.registration_date, date_format); col += 1
        worksheet.write(row, col, registration.status); col += 1
        worksheet.write(row, col, (registration.program.title if registration.program else (program.title if program else ''))); col += 1
        worksheet.write(row, col, (registration.program.location if registration.program else (program.location if program else ''))); col += 1
        worksheet.write(row, col, registration.notes); col += 1
        row += 1
    
    # Adjust column widths for better readability
    for i, header in enumerate(headers):
        worksheet.set_column(i, i, len(header) + 2)
    
    # Close the workbook
    workbook.close()
    
    # Rewind the buffer
    output.seek(0)
    
    # Set up the HttpResponse
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{program.title.replace(" ", "_")}_registrants.xlsx"'
    
    return response


@login_required
def export_registrants_pdf(request, registrations=None, program=None):
    """Export program registrants to PDF"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If registrations not provided, get from program_id
    if registrations is None and program is None:
        program_id = request.GET.get('program_id')
        if not program_id:
            messages.error(request, 'Program ID is required.')
            return redirect('program_list')
        
        program = get_object_or_404(AgricultureProgram, id=program_id)
        registrations = Registration.objects.filter(program=program).order_by('-registration_date')
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Add title
    title = Paragraph(f"Registrants for {program.title}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Styles for table content
    body_style = ParagraphStyle(name='BodySmall', fontSize=8, leading=10)
    header_style = ParagraphStyle(name='HeaderSmall', fontSize=9, leading=11)

    headers = [
        'Username', 'Name', 'Email', 'Registration Date', 'Status', 'Program', 'Program Location'
    ]
    data = [[Paragraph(h, header_style) for h in headers]]

    for registration in registrations:
        name = Paragraph(f"{registration.user.first_name} {registration.user.last_name}", body_style)
        email = Paragraph(registration.user.email, body_style)
        prog_title = Paragraph((registration.program.title if registration.program else (program.title if program else '')), body_style)
        prog_loc = Paragraph((registration.program.location if registration.program else (program.location if program else '')), body_style)
        data.append([
            registration.user.username,
            name,
            email,
            registration.registration_date.strftime('%Y-%m-%d'),
            registration.status,
            prog_title,
            prog_loc
        ])

    # Fit columns to available page width
    page_width, _ = landscape(letter)
    content_width = page_width - (30 + 30)
    weights = [80, 110, 150, 80, 60, 120, 120]
    scale = content_width / float(sum(weights))
    col_widths = [w * scale for w in weights]

    table = Table(data, colWidths=col_widths)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    
    # Apply alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
    
    table.setStyle(style)
    elements.append(table)
    
    # Build the document
    doc.build(elements)
    
    # Get the value of the buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{program.title.replace(" ", "_")}_registrants.pdf"'
    response.write(pdf)
    
    return response


@login_required
def registration_detail(request, registration_id):
    """View details of a specific registration"""
    # Check if user has staff privilege or is the owner of the registration
    registration = get_object_or_404(Registration, id=registration_id)
    
    if not request.user.is_staff and request.user != registration.user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    return render(request, 'registration_detail.html', {
        'registration': registration,
        'program': registration.program,
        'user': registration.user,
    })


@login_required
def notifications(request):
    """View all notifications for a user"""
    notification_type = request.GET.get('type', None)
    
    # Base queryset
    notifications_queryset = Notification.objects.filter(user=request.user)
    
    # Clean up old notifications automatically (older than 30 days)
    Notification.clear_old_notifications(request.user)
    
    # Apply filter if requested
    if notification_type in [Notification.INFO, Notification.SUCCESS, Notification.WARNING, Notification.ERROR]:
        notifications_queryset = notifications_queryset.filter(notification_type=notification_type)
    
    # Order by created date (newest first) and read status (unread first)
    notifications = notifications_queryset.order_by('read', '-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)  # Show 20 notifications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications.html', {
        'notifications': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'current_type': notification_type,
        'notification_types': [
            {'code': Notification.INFO, 'name': 'Information'},
            {'code': Notification.SUCCESS, 'name': 'Success'},
            {'code': Notification.WARNING, 'name': 'Warning'},
            {'code': Notification.ERROR, 'name': 'Error'},
        ]
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        # Get updated unread count
        unread_count = Notification.objects.filter(user=request.user, read=False).count()
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    
    # Redirect to notification source if available, otherwise to the home page
    return redirect(notification.link if notification.link else 'index')


@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    # Apply type filter if present
    notification_type = request.GET.get('type', None)
    filter_kwargs = {'user': request.user, 'read': False}
    
    if notification_type in [Notification.INFO, Notification.SUCCESS, Notification.WARNING, Notification.ERROR]:
        filter_kwargs['notification_type'] = notification_type
    
    Notification.objects.filter(**filter_kwargs).update(read=True)
    
    messages.success(request, 'All notifications have been marked as read.')
    
    # Redirect back with type filter if it was present
    redirect_url = 'notifications'
    if notification_type:
        redirect_url += f'?type={notification_type}'
    return redirect(redirect_url)


@login_required
def delete_notification(request, notification_id):
    """Delete a specific notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    messages.success(request, 'Notification deleted.')
    
    # Redirect back to notifications page with any active filters
    notification_type = request.GET.get('type', None)
    redirect_url = 'notifications'
    if notification_type:
        redirect_url += f'?type={notification_type}'
    return redirect(redirect_url)


@login_required
def delete_all_notifications(request):
    """Delete all notifications for a user"""
    # Apply type filter if present
    notification_type = request.GET.get('type', None)
    filter_kwargs = {'user': request.user}
    
    if notification_type in [Notification.INFO, Notification.SUCCESS, Notification.WARNING, Notification.ERROR]:
        filter_kwargs['notification_type'] = notification_type
    
    Notification.objects.filter(**filter_kwargs).delete()
    
    messages.success(request, 'All notifications have been deleted.')
    
    # Redirect back with type filter if it was present
    redirect_url = 'notifications'
    if notification_type:
        redirect_url += f'?type={notification_type}'
    return redirect(redirect_url)


@login_required
def update_registration_status(request, registration_id, status):
    """Update the status of a registration"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    registration = get_object_or_404(Registration, id=registration_id)
    
    if status not in [Registration.PENDING, Registration.APPROVED, Registration.REJECTED]:
        messages.error(request, 'Invalid status.')
        return redirect('registration_detail', registration_id=registration_id)
    
    registration.status = status
    registration.save()
    
    status_display = dict(Registration.STATUS_CHOICES)[status]
    messages.success(request, f'Registration status updated to {status_display}.')
    
    # Notify the user about the status change
    Notification.add_notification(
        user=registration.user,
        message=f"Your registration for {registration.program.title} has been {status_display.lower()}.",
        notification_type=Notification.INFO if status == Registration.PENDING else (
            Notification.SUCCESS if status == Registration.APPROVED else Notification.ERROR
        ),
        link=f"/registrations/{registration.id}/"
    )
    
    return redirect('registration_detail', registration_id=registration_id)


@login_required
def update_candidate_status(request, candidate_id, status):
    """Update the status of a candidate (admin only)"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Normalize status (convert to proper case: 'approved' -> 'Approved', 'rejected' -> 'Rejected')
    status_map = {
        'approved': Candidate.APPROVED,
        'rejected': Candidate.REJECTED,
    }
    
    normalized_status = status_map.get(status.lower())
    
    if not normalized_status:
        messages.error(request, 'Invalid status. Only Approved or Rejected statuses are allowed.')
        return redirect('view_candidate', candidate_id=candidate_id)
    
    candidate.status = normalized_status
    candidate.save()
    
    status_display = dict(Candidate.STATUS_CHOICES)[normalized_status]
    messages.success(request, f'{candidate.first_name} {candidate.last_name}\'s status has been updated to {status_display}.')
    
    # Find the actual applicant to notify (not the admin who created the candidate record)
    applicant_user = None
    
    # Try to find the user by email if candidate has an email
    if candidate.email:
        applicant_user = User.objects.filter(email=candidate.email).first()
    
    # If not found by email, try to find via Registration
    if not applicant_user and candidate.program:
        registration = Registration.objects.filter(
            program=candidate.program,
            processed=True
        ).first()
        if registration:
            applicant_user = registration.user
    
    # Only notify if we found the actual applicant (not the admin)
    if applicant_user and applicant_user != candidate.created_by:
        notification_type = Notification.SUCCESS if normalized_status == Candidate.APPROVED else Notification.ERROR
        Notification.add_notification(
            user=applicant_user,
            message=f"Your application has been {status_display.lower()}.",
            notification_type=notification_type,
            link=f"/candidates/{candidate.id}/"
        )
    
    return redirect('view_candidate', candidate_id=candidate_id)


@login_required
def api_notifications(request):
    """API endpoint to get notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]  # Get the 10 most recent
    
    # Format notifications for JSON response
    notifications_data = []
    for notification in notifications:
        # Format the created_at date
        created_at_formatted = notification.created_at.strftime('%b %d, %Y %H:%M')
        
        notifications_data.append({
            'id': notification.id,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'link': notification.link,
            'created_at': created_at_formatted,
            'read': notification.read,
        })
    
    return JsonResponse({'notifications': notifications_data})


@login_required
def api_clear_all_notifications(request):
    """API endpoint to clear all notifications for the current user"""
    if request.user.is_authenticated:
        Notification.objects.filter(user=request.user).delete()
        return JsonResponse({
            'success': True,
            'message': 'All notifications cleared successfully.'
        })
    return JsonResponse({
        'success': False,
        'message': 'Authentication required.'
    }, status=403)


@require_GET
def check_username(request):
    """API endpoint to check if a username is available"""
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({
            'available': False,
            'message': 'Username cannot be empty'
        })
        
    # Check if username meets the requirements
    import re
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return JsonResponse({
            'available': False,
            'message': 'Username must be 3-20 characters using only letters, numbers, and underscores'
        })
    
    # Check if username exists
    exists = User.objects.filter(username=username).exists()
    return JsonResponse({
        'available': not exists,
        'message': 'Username is available' if not exists else 'Username is already taken'
    })


@require_POST
def ajax_login(request):
    """API endpoint for AJAX login"""
    try:
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Create profile if it doesn't exist (for backward compatibility)
                try:
                    profile = Profile.objects.get(user=user)
                except Profile.DoesNotExist:
                    Profile.objects.create(user=user, email_verified=True)
                
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': f'Welcome back, {username}!',
                    'redirect': '/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': ['Invalid username or password.']}
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': {k: [str(e) for e in v] for k, v in form.errors.items()}
            })
    except Exception as e:
        logger.error(f"AJAX login error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'errors': {'__all__': [f'Server error: {str(e)}']}
        }, status=500)


@require_POST
def ajax_register(request):
    """API endpoint for AJAX registration using comprehensive form"""
    form = ComprehensiveRegisterForm(request.POST, request.FILES)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        
        # Check if a user with this username or email already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'errors': {'username': [f'An account with username "{username}" already exists. Please choose a different username.']}
            })
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'errors': {'email': [f'An account with email "{email}" already exists. Please use a different email or try to log in.']}
            })
        
        # Save user and profile
        user = form.save()
        profile = form.save_profile(user)
        
        # Mark email as verified
        profile.email_verified = True
        profile.save()
        
        # Create welcome notification
        Notification.add_notification(
            user=user,
            message="Welcome to AgroStudies! Your comprehensive profile has been created successfully.",
            notification_type=Notification.SUCCESS,
            link="/profile/"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Account created for {username}! Your profile is now complete. You can log in.',
            'redirect': '/?auto_open_modal=login'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': {k: [str(e) for e in v] for k, v in form.errors.items()}
        })


@login_required
def get_user_applications(request):
    """API endpoint to get user's program applications"""
    registrations = Registration.objects.filter(user=request.user).select_related('program')
    data = [{
        'id': reg.id,
        'program_name': reg.program.title,
        'program_id': reg.program.id,
        'status': reg.get_status_display(),
        'status_code': reg.status,
        'application_date': reg.created_at.strftime('%Y-%m-%d'),
        'last_updated': reg.updated_at.strftime('%Y-%m-%d %H:%M')
    } for reg in registrations]
    
    return JsonResponse({
        'success': True,
        'applications': data
    })


def modal_login(request):
    """Return login form HTML for modal"""
    form = AuthenticationForm()
    return render(request, 'modals/login_modal.html', {'form': form})


def modal_register(request):
    """Return comprehensive registration form HTML for modal with OAuth data if available"""
    from .oauth_utils import get_oauth_session_data
    
    # Get OAuth data from session if available
    oauth_data = get_oauth_session_data(request)
    
    # Pre-populate form with OAuth data if available
    if oauth_data:
        initial_data = {
            'email': oauth_data.get('email'),
            'confirm_email': oauth_data.get('email'),
            'first_name': oauth_data.get('first_name'),
            'last_name': oauth_data.get('last_name'),
        }
        form = ComprehensiveRegisterForm(initial=initial_data)
        logger.info(f"Modal register form pre-filled with OAuth data for {oauth_data.get('email')}")
    else:
        form = ComprehensiveRegisterForm()
    
    # Clear the auto-open modal flag after loading the form
    if 'auto_open_register_modal' in request.session:
        del request.session['auto_open_register_modal']
        request.session.modified = True
    
    return render(request, 'modals/register_modal.html', {
        'form': form,
        'oauth_data': oauth_data
    })


def modal_admin_register(request):
    """Return admin registration form HTML for modal"""
    form = AdminRegistrationForm()
    return render(request, 'modals/admin_register_modal.html', {'form': form})


@require_POST
def ajax_admin_register(request):
    """API endpoint for AJAX admin registration"""
    form = AdminRegistrationForm(request.POST)
    if form.is_valid():
        user = form.save()
        # Profile auto-created by signal, no need to create manually
        username = form.cleaned_data.get('username')
        
        return JsonResponse({
            'success': True,
            'message': f'Admin account created for {username}! You can now log in.',
            'redirect': '/?auto_open_modal=login'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': {k: [str(e) for e in v] for k, v in form.errors.items()}
        })


def custom_password_reset(request):
    """
    Custom password reset view with email validation
    """
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            # Email exists and is valid, send reset email
            try:
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name='password_reset_email.html',
                    subject_template_name='password_reset_subject.txt'
                )
                messages.success(
                    request,
                    'Password reset email has been sent. Please check your inbox.'
                )
                return redirect('password_reset_done')
            except Exception as e:
                logging.error(f"Error sending password reset email: {e}")
                messages.error(
                    request,
                    'There was an error sending the password reset email. Please try again later.'
                )
        else:
            # Form has errors (email not found)
            for error in form.errors.get('email', []):
                messages.warning(request, error)
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'password_reset.html', {'form': form})


# ============================================================================
# OAuth 2.0 Social Authentication Views
# ============================================================================

def social_register(request):
    """
    Social authentication gateway page
    Displays OAuth provider options and email signup option
    """
    import logging
    from django.conf import settings
    from allauth.socialaccount.models import SocialApp
    
    logger = logging.getLogger(__name__)
    
    # Get OAuth credentials from database (django-allauth SocialApp)
    try:
        google_app = SocialApp.objects.get(provider='google')
        google_client_id = google_app.client_id
        logger.info(f"Google OAuth loaded: {google_client_id[:30]}...")
    except SocialApp.DoesNotExist:
        google_client_id = ''
        logger.error("Google SocialApp not found in database")
    
    try:
        facebook_app = SocialApp.objects.get(provider='facebook')
        facebook_client_id = facebook_app.client_id
        logger.info(f"Facebook OAuth loaded: {facebook_client_id[:30]}...")
    except SocialApp.DoesNotExist:
        facebook_client_id = ''
        logger.warning("Facebook SocialApp not found in database")
    
    try:
        microsoft_app = SocialApp.objects.get(provider='microsoft')
        microsoft_client_id = microsoft_app.client_id
        logger.info(f"Microsoft OAuth loaded: {microsoft_client_id[:30]}...")
    except SocialApp.DoesNotExist:
        microsoft_client_id = ''
        logger.warning("Microsoft SocialApp not found in database")
    
    context = {
        'GOOGLE_OAUTH_CLIENT_ID': google_client_id,
        'FACEBOOK_OAUTH_CLIENT_ID': facebook_client_id,
        'MICROSOFT_OAUTH_CLIENT_ID': microsoft_client_id,
    }
    logger.info(f"Context keys: {list(context.keys())}")
    
    # Clear the auto-open flag after rendering (will be used by template)
    if request.session.get('auto_open_register_modal'):
        # Don't clear it yet - let the template use it first
        # It will be cleared when the modal loads
        pass
    
    return render(request, 'register-email.html', context)


def oauth_initiate(request, provider):
    """
    Server-side OAuth initiation - generates state, stores in session, redirects to provider
    """
    import secrets
    from allauth.socialaccount.models import SocialApp
    from urllib.parse import urlencode
    
    # Generate and store state in Django session
    state = secrets.token_urlsafe(32)
    request.session[f'oauth_state_{provider}'] = state
    request.session.modified = True
    
    # Build redirect URI
    redirect_uri = request.build_absolute_uri(f'/auth/{provider}/callback/')
    
    # Get OAuth config based on provider
    try:
        if provider == 'google':
            app = SocialApp.objects.get(provider='google')
            auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
            params = {
                'client_id': app.client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'openid email profile',
                'state': state,
                'access_type': 'online',
                'prompt': 'consent'
            }
        elif provider == 'facebook':
            app = SocialApp.objects.get(provider='facebook')
            auth_url = 'https://www.facebook.com/v15.0/dialog/oauth'
            params = {
                'client_id': app.client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'email,public_profile',
                'state': state,
            }
        elif provider == 'microsoft':
            app = SocialApp.objects.get(provider='microsoft')
            auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
            params = {
                'client_id': app.client_id,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'scope': 'openid profile email',
                'state': state,
                'response_mode': 'query'
            }
        else:
            messages.error(request, f"Unknown OAuth provider: {provider}")
            return redirect('social_register')
            
    except SocialApp.DoesNotExist:
        logger.error(f"SocialApp not found for provider: {provider}")
        messages.error(request, f"{provider.title()} sign-in is not configured. Please use email registration.")
        return redirect('social_register')
    
    # Redirect to OAuth provider
    oauth_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"Redirecting to {provider} OAuth: {oauth_url[:100]}...")
    return redirect(oauth_url)


def oauth_callback(request, provider):
    """
    Generic OAuth callback handler for all providers
    Processes authorization code and redirects to registration form
    Called after user authorizes with OAuth provider
    """
    from .oauth_utils import (
        OAuthTokenExchanger, OAuthDataExtractor,
        store_oauth_session_data, ProfilePictureDownloader
    )
    
    # Get authorization code and state
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')
    
    # Check for OAuth errors
    if error:
        logger.warning(f"OAuth error from {provider}: {error} - {error_description}")
        messages.error(request, f"Authentication failed: {error_description or error}")
        return redirect('social_register')
    
    # Validate state parameter
    session_state = request.session.get(f'oauth_state_{provider}')
    if not state or state != session_state:
        logger.warning(f"State mismatch for {provider}")
        messages.error(request, "Authentication state mismatch. Please try again.")
        return redirect('social_register')
    
    if not code:
        messages.error(request, "No authorization code received from provider.")
        return redirect('social_register')
    
    try:
        # Build redirect URI
        redirect_uri = request.build_absolute_uri(f'/auth/{provider}/callback/')
        
        # Exchange code for access token
        if provider == 'google':
            access_token, id_token = OAuthTokenExchanger.exchange_google_code(code, redirect_uri)
            user_data = OAuthDataExtractor.get_google_user_data(access_token) if access_token else None
        elif provider == 'facebook':
            access_token, _ = OAuthTokenExchanger.exchange_facebook_code(code, redirect_uri)
            user_data = OAuthDataExtractor.get_facebook_user_data(access_token) if access_token else None
        elif provider == 'microsoft':
            access_token, _ = OAuthTokenExchanger.exchange_microsoft_code(code, redirect_uri)
            user_data = OAuthDataExtractor.get_microsoft_user_data(access_token) if access_token else None
        else:
            messages.error(request, f"Unknown OAuth provider: {provider}")
            return redirect('social_register')
        
        if not access_token or not user_data:
            logger.error(f"Failed to retrieve OAuth data for {provider}")
            messages.error(request, f"Failed to authenticate with {provider.title()}. Please try again.")
            return redirect('social_register')
        
        # Store OAuth data in session
        store_oauth_session_data(request, user_data)
        
        # Set flag to auto-open modal
        request.session['auto_open_register_modal'] = True
        request.session.modified = True
        
        # Redirect back to social register page which will auto-open the modal
        return redirect('social_register')
        
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}")
        messages.error(request, f"An error occurred during authentication. Please try again.")
        return redirect('social_register')


def oauth_callback_get(request, provider):
    """
    GET handler for OAuth callback (redirects via POST)
    OAuth providers typically redirect via GET
    """
    # Convert GET request to POST for processing
    post_request = request.POST.copy()
    post_request.update(request.GET)
    
    # Create a new request object with the combined data
    class ModifiedRequest:
        def __init__(self, original_request):
            self.__dict__.update(original_request.__dict__)
            self.POST = post_request
            self.GET = original_request.GET
        
        def build_absolute_uri(self, location):
            return self.META['wsgi.url_scheme'] + '://' + self.META['HTTP_HOST'] + location
        
        def __getattr__(self, name):
            return getattr(self._request, name)
    
    modified_request = ModifiedRequest(request)
    return oauth_callback(modified_request, provider)

