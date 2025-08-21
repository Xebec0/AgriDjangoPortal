from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.forms import AuthenticationForm
from .models import Profile, AgricultureProgram, Registration, Candidate, University, Notification
from .models import ActivityLog
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm, 
    ProgramRegistrationForm, AdminRegistrationForm,
    CandidateForm, CandidateSearchForm, ProgramSearchForm
)
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


def index(request):
    """Home page view"""
    programs = AgricultureProgram.objects.all().order_by('-start_date')[:5]
    return render(request, 'index.html', {'programs': programs})


def register(request):
    """User registration view without email verification"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            
            # Check if a user with this username or email already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f'An account with username "{username}" already exists. Please choose a different username.')
                return render(request, 'register.html', {'form': form})
            
            if User.objects.filter(email=email).exists():
                messages.error(request, f'An account with email "{email}" already exists. Please use a different email or try to log in.')
                return render(request, 'register.html', {'form': form})
            
            # Create the user if it doesn't exist
            user = form.save()
            
            # The profile will be automatically created by signals.py
            # Just ensure it's marked as email verified
            profile = Profile.objects.get(user=user)
            profile.email_verified = True
            profile.save()
            
            # Create welcome notification
            Notification.add_notification(
                user=user,
                message="Welcome to AgroStudies! Your account has been created successfully.",
                notification_type=Notification.SUCCESS,
                link="/"
            )
            
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


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


def admin_register(request):
    """Admin registration view"""
    if request.method == 'POST':
        form = AdminRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile for admin
            Profile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Admin account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = AdminRegistrationForm()
    return render(request, 'admin_register.html', {'form': form})


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
            except Exception:
                # Best-effort sync; do not block profile save on errors
                pass

            # Create a notification
            Notification.add_notification(
                request.user,
                "Your profile has been successfully updated.",
                Notification.SUCCESS
            )
            
            return redirect('profile')
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
        'candidate_apps': candidate_apps
    }
    return render(request, 'profile.html', context)


def program_list(request):
    """List all available programs"""
    programs = AgricultureProgram.objects.all().order_by('-start_date')
    form = ProgramSearchForm(request.GET)

    if form.is_valid():
        query = form.cleaned_data.get('query')
        location = form.cleaned_data.get('location')

        if query:
            programs = programs.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        if location:
            programs = programs.filter(location__icontains=location)

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
    
    return render(request, 'program_list.html', {
        'page_obj': page_obj,
        'applied_program_ids': applied_program_ids,
        'has_applied_any': has_applied_any,
        'form': form,
    })


def program_detail(request, program_id):
    """Show details of a specific program"""
    program = get_object_or_404(AgricultureProgram, id=program_id)
    
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
    """Applicant-facing: single-step application that creates a Candidate directly and redirects to candidates list."""
    program = get_object_or_404(AgricultureProgram, id=program_id)

    # New guard: Check program capacity
    if program.capacity <= 0:
        messages.error(request, 'This program has no available slots.', extra_tags='error')
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
        # Pre-fill POST with current user info to keep profile -> application in sync
        mutable_post = request.POST.copy()
        mutable_post['first_name'] = request.user.first_name or mutable_post.get('first_name', '')
        mutable_post['confirm_first_name'] = request.user.first_name or mutable_post.get('confirm_first_name', '')
        mutable_post['last_name'] = request.user.last_name or mutable_post.get('last_name', '')
        mutable_post['confirm_surname'] = request.user.last_name or mutable_post.get('confirm_surname', '')
        mutable_post['email'] = request.user.email or mutable_post.get('email', '')
        form = CandidateForm(mutable_post, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.created_by = request.user
            candidate.program = program
            candidate.status = Candidate.APPROVED
            
            # Decrease program capacity
            program.capacity -= 1
            program.save()
            
            candidate.save()

            messages.success(request, f'Congratulations! Your application for {program.title} has been approved.')
            
            # Create a notification for the user
            Notification.add_notification(
                user=request.user,
                message=f"Congratulations! Your application for {program.title} has been approved. You're now ready to proceed with the next steps.",
                notification_type=Notification.SUCCESS,
                link=f"/candidates/{candidate.id}/"
            )
            
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # Prefill from user if available
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'confirm_first_name': request.user.first_name,
            'confirm_surname': request.user.last_name,
            'father_name': request.user.profile.father_name,
            'mother_name': request.user.profile.mother_name,
            'date_of_birth': request.user.profile.date_of_birth,
            'gender': request.user.profile.gender,
            'country_of_birth': request.user.profile.country_of_birth,
            'nationality': request.user.profile.nationality,
            'religion': request.user.profile.religion,
        }
        form = CandidateForm(initial=initial_data)

    return render(request, 'candidate_form.html', {
        'form': form,
        'title': f'Apply to {program.title}',
        'button_text': 'Submit Application'
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
        candidates = Candidate.objects.all().order_by('-created_at')
    else:
        # Show only the current user's candidate records
        candidates = Candidate.objects.filter(
            Q(created_by=request.user) | Q(email=request.user.email)
        ).order_by('-created_at')
    form = CandidateSearchForm(request.GET)
    
    # Apply filters (staff only)
    if form.is_valid() and request.user.is_staff:
        # Filter by country (university's country)
        country = form.cleaned_data.get('country')
        if country:
            candidates = candidates.filter(university__country=country)
        
        # Filter by university
        university = form.cleaned_data.get('university')
        if university:
            candidates = candidates.filter(university__code=university)
        
        # Filter by specialization
        specialization = form.cleaned_data.get('specialization')
        if specialization:
            candidates = candidates.filter(specialization=specialization)
        
        # Filter by status
        status = form.cleaned_data.get('status')
        if status:
            candidates = candidates.filter(status=status)
        
        # Filter by passport number
        passport = form.cleaned_data.get('passport')
        if passport:
            candidates = candidates.filter(passport_number__icontains=passport)
    
    # Check if export is requested
    export_format = request.GET.get('export')
    if export_format:
        if export_format == 'csv':
            return export_candidates_csv(request, candidates)
        elif export_format == 'excel':
            return export_candidates_excel(request, candidates)
        elif export_format == 'pdf':
            return export_candidates_pdf(request, candidates)
    
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
            'Fixed': 'primary',
            'Approved': 'success',
            'Rejected': 'danger',
            'Quit': 'warning'
        }
    })


@login_required
def export_candidates_csv(request, candidates=None):
    """Export candidates to CSV file"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.all().order_by('-created_at')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="candidates.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Passport Number', 'First Name', 'Last Name', 'Email', 'Date of Birth',
        'Gender', 'Nationality', 'University', 'Specialization', 'Status',
        'Program', 'Program Location', 'Date Added'
    ])
    
    for candidate in candidates:
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
    """Export candidates to Excel file"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.all().order_by('-created_at')
    
    # Create an in-memory output file
    output = BytesIO()
    
    # Create a workbook and add a worksheet with remove_timezone option
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
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
    
    # Write data rows
    for candidate in candidates:
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
    """Export candidates to PDF file"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    # If candidates not provided, get all (used when directly accessing the export URL)
    if candidates is None:
        candidates = Candidate.objects.all().order_by('-created_at')
    
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
    
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f'Candidate {candidate.first_name} {candidate.last_name} has been updated successfully.')
            return redirect('candidate_list')
    else:
        form = CandidateForm(instance=candidate)
    
    return render(request, 'candidate_form.html', {
        'form': form,
        'candidate': candidate,
        'title': f'Edit Candidate: {candidate.first_name} {candidate.last_name}',
        'button_text': 'Update Candidate'
    })


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
        'Fixed': 'primary',
        'Approved': 'success',
        'Rejected': 'danger',
        'Quit': 'warning'
    }
    
    # Check if there's a POST request for importing a document
    if request.method == 'POST' and 'import_document' in request.POST:
        doc_type = request.POST.get('document_type')
        registration_id = request.POST.get('registration_id')
        
        from core.utils import import_document_to_candidate
        success = import_document_to_candidate(candidate, doc_type, registration_id)
        
        if success:
            messages.success(request, f'Successfully imported {doc_type.replace("_", " ").title()} document.')
        else:
            messages.error(request, f'Failed to import document. Please try again.')
        
        return redirect('view_candidate', candidate_id=candidate.id)
    
    # Scan for available documents from the user's registrations
    from core.utils import get_available_documents
    documents = get_available_documents(candidate)
    
    # Fetch recent audit logs for this candidate (admin-only page)
    activity_logs = ActivityLog.objects.filter(
        model_name='core.Candidate',
        object_id=str(candidate.id)
    ).order_by('-timestamp')[:50]

    return render(request, 'candidate_detail.html', {
        'candidate': candidate,
        'status_color': status_colors.get(candidate.status, 'secondary'),
        'documents': documents,
        'activity_logs': activity_logs,
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
            'Fixed': 'primary',
            'Approved': 'success',
            'Rejected': 'danger',
            'Quit': 'warning'
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


@require_POST
def ajax_register(request):
    """API endpoint for AJAX registration"""
    form = UserRegisterForm(request.POST)
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
        
        # Create the user if it doesn't exist
        user = form.save()
        
        # The profile will be automatically created by signals.py
        # Just ensure it's marked as email verified
        profile = Profile.objects.get(user=user)
        profile.email_verified = True
        profile.save()
        
        # Create welcome notification
        Notification.add_notification(
            user=user,
            message="Welcome to AgroStudies! Your account has been created successfully.",
            notification_type=Notification.SUCCESS,
            link="/"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Account created for {username}! You can now log in.',
            'redirect': '/login/'
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
    """Return registration form HTML for modal"""
    form = UserRegisterForm()
    return render(request, 'modals/register_modal.html', {'form': form})


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
        # Create profile for admin
        Profile.objects.create(user=user)
        username = form.cleaned_data.get('username')
        
        return JsonResponse({
            'success': True,
            'message': f'Admin account created for {username}! You can now log in.',
            'redirect': '/login/'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': {k: [str(e) for e in v] for k, v in form.errors.items()}
        })
