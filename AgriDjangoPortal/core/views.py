from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from .models import Profile, AgricultureProgram, Registration, Candidate, University
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm, 
    ProgramRegistrationForm, AdminRegistrationForm,
    CandidateForm, CandidateSearchForm
)


def index(request):
    """Home page view"""
    programs = AgricultureProgram.objects.all().order_by('-start_date')[:5]
    return render(request, 'index.html', {'programs': programs})


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile
            Profile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


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
    """Login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
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
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
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
        form = ProgramRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.user = request.user
            registration.program = program
            registration.save()
            messages.success(request, f'Successfully registered for {program.title}!')
            return redirect('profile')
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
def add_candidate(request):
    """Add a new candidate"""
    # Check if user has staff privilege
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('index')
    
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.created_by = request.user
            candidate.status = 'Draft'  # Set initial status
            candidate.save()
            messages.success(request, f'Candidate {candidate.first_name} {candidate.last_name} has been added successfully.')
            return redirect('candidate_list')
    else:
        form = CandidateForm()
    
    return render(request, 'candidate_form.html', {
        'form': form,
        'title': 'Add New Candidate',
        'button_text': 'Add Candidate'
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
    
    return render(request, 'candidate_detail.html', {
        'candidate': candidate,
        'status_color': status_colors.get(candidate.status, 'secondary')
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
    
    candidate.status = status
    candidate.save()
    
    messages.success(request, f'Status for {candidate.first_name} {candidate.last_name} has been changed to {status}.')
    return redirect('view_candidate', candidate_id=candidate_id)


def help_page(request):
    """Registration help page"""
    return render(request, 'help.html')


def contact_page(request):
    """Contact page"""
    return render(request, 'contact.html')
