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
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm, 
    ProgramRegistrationForm, AdminRegistrationForm,
    CandidateForm, CandidateSearchForm
)
import csv
import xlsxwriter
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import uuid
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
import os
import json


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
    
    # Get user registrations
    registrations = Registration.objects.filter(user=request.user).order_by('-registration_date')
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'registrations': registrations
    }
    return render(request, 'profile.html', context)


def program_list(request):
    """List all available programs"""
    programs = AgricultureProgram.objects.all().order_by('-start_date')
    
    # Pagination
    paginator = Paginator(programs, 10)  # Show 10 programs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'program_list.html', {'page_obj': page_obj})


def program_detail(request, program_id):
    """Show details of a specific program"""
    program = get_object_or_404(AgricultureProgram, id=program_id)
    
    # Check if user is already registered
    user_registered = False
    registration = None
    if request.user.is_authenticated:
        try:
            registration = Registration.objects.get(user=request.user, program=program)
            user_registered = True
        except Registration.DoesNotExist:
            pass
    
    return render(request, 'program_detail.html', {
        'program': program,
        'user_registered': user_registered,
        'registration': registration
    })


@login_required
def program_register(request, program_id):
    """Register for a program"""
    program = get_object_or_404(AgricultureProgram, id=program_id)
    
    # Check if already registered
    try:
        Registration.objects.get(user=request.user, program=program)
        messages.warning(request, 'You are already registered for this program.')
        return redirect('program_detail', program_id=program_id)
    except Registration.DoesNotExist:
        pass
    
    if request.method == 'POST':
        # Include request.FILES for file uploads
        form = ProgramRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.user = request.user
            registration.program = program
            
            # Save the registration to get an ID
            registration.save()
            
            # Try to find a candidate profile for this user
            try:
                # Assuming the user's email is used to match with candidate's email
                candidate = Candidate.objects.get(email=request.user.email)
                # Copy the uploaded documents to the candidate profile
                registration.copy_documents_to_candidate(candidate)
                messages.info(request, 'Your documents have been linked to your candidate profile.')
            except Candidate.DoesNotExist:
                # No candidate profile found, just continue
                pass
            
            # Notify all admin users about the new registration
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.add_notification(
                    user=admin,
                    message=f"New registration: {request.user.username} has registered for {program.title}",
                    notification_type=Notification.INFO,
                    link=f"/registrations/{registration.id}/"
                )
            
            messages.success(request, f'Successfully registered for {program.title}! Your documents have been submitted.')
            return redirect('profile')
        else:
            # If form is invalid, display errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = ProgramRegistrationForm()
    
    return render(request, 'program_register.html', {'form': form, 'program': program})


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
    """List all candidates with search and filter functionality"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    candidates = Candidate.objects.all().order_by('-created_at')
    form = CandidateSearchForm(request.GET)
    
    # Apply filters
    if form.is_valid():
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
        'Date Added'
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
        'Smokes', 'Status', 'Date Added'
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
    
    # Create data for table
    data = [
        [
            'Passport Number', 'Name', 'Nationality', 'University', 
            'Specialization', 'Status', 'Date Added'
        ]
    ]
    
    # Add data rows
    for candidate in candidates:
        data.append([
            candidate.passport_number,
            f"{candidate.first_name} {candidate.last_name}",
            candidate.nationality,
            candidate.university.name,
            candidate.specialization,
            candidate.status,
            candidate.created_at.strftime('%Y-%m-%d')
        ])
    
    # Create the table
    table = Table(data)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
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
    
    return render(request, 'candidate_detail.html', {
        'candidate': candidate,
        'status_color': status_colors.get(candidate.status, 'secondary'),
        'documents': documents
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


@login_required
def change_candidate_status(request, candidate_id, status):
    """Change candidate status"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # Validate status
    valid_statuses = ['Draft', 'New', 'Fixed', 'Approved', 'Rejected', 'Quit']
    if status not in valid_statuses:
        messages.error(request, 'Invalid status value.')
        return redirect('view_candidate', candidate_id=candidate_id)
    
    # Store the old status for notification message and capacity management
    old_status = candidate.status
    
    # Handle program capacity changes
    if candidate.program:
        program = candidate.program
        
        # Case 1: Candidate was approved and is now being changed to something else
        # Increase capacity by 1
        if old_status == 'Approved' and status != 'Approved':
            program.capacity += 1
            program.save()
            messages.info(request, f'Program capacity for {program.title} has been increased to {program.capacity}.')
        
        # Case 2: Candidate was not approved and is now being approved
        # Decrease capacity by 1
        elif old_status != 'Approved' and status == 'Approved':
            if program.capacity > 0:  # Make sure we don't go below zero
                program.capacity -= 1
                program.save()
                messages.info(request, f'Program capacity for {program.title} has been decreased to {program.capacity}.')
    
    # Update the status
    candidate.status = status
    candidate.save()
    
    # Try to find the user associated with this candidate by email
    if candidate.email:
        try:
            user = User.objects.get(email=candidate.email)
            
            # Determine notification type and message based on status
            if status == 'Approved':
                notification_type = Notification.SUCCESS
                message = f"Congratulations! Your application has been approved. You're now ready to proceed with the next steps."
            elif status == 'Rejected':
                notification_type = Notification.ERROR
                message = f"We regret to inform you that your application has been declined. Please contact the administration for more details."
            elif status == 'Quit':
                notification_type = Notification.ERROR
                message = f"Your application has been marked as withdrawn. If this was a mistake, please contact the administration."
            elif status == 'Fixed':
                notification_type = Notification.INFO
                message = f"Your application has been reviewed and marked as fixed. It will now proceed to the next stage of evaluation."
            elif status == 'New':
                notification_type = Notification.INFO
                message = f"Your application has been received and is now under review. We'll update you on any progress."
            else:
                notification_type = Notification.INFO
                message = f"Your application status has been updated to {status}. Please check your profile for more details."
            
            # Create a notification for the user
            Notification.add_notification(
                user=user,
                message=message,
                notification_type=notification_type,
                link=f"/candidates/{candidate.id}/"
            )
        except User.DoesNotExist:
            # No user found with this email, can't send notification
            pass
    
    messages.success(request, f'Status for {candidate.first_name} {candidate.last_name} has been changed to {status}.')
    return redirect('view_candidate', candidate_id=candidate_id)


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
    # Only show registrations that haven't been processed into candidates
    registrations = Registration.objects.filter(program=program, processed=False).order_by('-registration_date')
    
    # Check if export is requested
    export_format = request.GET.get('export')
    if export_format:
        if export_format == 'csv':
            return export_registrants_csv(request, registrations, program)
        elif export_format == 'excel':
            return export_registrants_excel(request, registrations, program)
        elif export_format == 'pdf':
            return export_registrants_pdf(request, registrations, program)
    
    # Pagination
    paginator = Paginator(registrations, 20)  # Show 20 registrations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'program_registrants.html', {
        'program': program,
        'page_obj': page_obj,
        'status_colors': {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger',
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
        'Registration Date', 'Status', 'Notes'
    ])
    
    for registration in registrations:
        writer.writerow([
            registration.user.username,
            registration.user.first_name,
            registration.user.last_name,
            registration.user.email,
            registration.registration_date.strftime('%Y-%m-%d'),
            registration.status,
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
        'Registration Date', 'Status', 'Notes'
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
    
    # Create data for table
    data = [
        [
            'Username', 'Name', 'Email', 'Registration Date', 'Status'
        ]
    ]
    
    # Add data rows
    for registration in registrations:
        data.append([
            registration.user.username,
            f"{registration.user.first_name} {registration.user.last_name}",
            registration.user.email,
            registration.registration_date.strftime('%Y-%m-%d'),
            registration.status
        ])
    
    # Create the table
    table = Table(data)
    
    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
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
