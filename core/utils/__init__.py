"""
Utility functions for the core app.
"""
from .file_tracker import (
    register_model_files,
    get_uploaded_documents_display,
    check_file_already_uploaded,
    deactivate_file_record
)


def admin_dashboard(request, context):
    """
    Unfold admin dashboard callback.
    Customizes the admin dashboard with summary statistics.
    
    Args:
        request: Django request object
        context: Dictionary of dashboard context
        
    Returns:
        Enriched context dictionary with dashboard statistics
    """
    from django.contrib.auth.models import User
    from core.models import Candidate, Registration, AgricultureProgram
    
    # Get statistics for dashboard
    total_users = User.objects.filter(is_staff=False).count()
    total_candidates = Candidate.objects.count()
    total_registrations = Registration.objects.count()
    total_programs = AgricultureProgram.objects.count()
    
    # Get status breakdowns
    pending_registrations = Registration.objects.filter(status='pending').count()
    approved_registrations = Registration.objects.filter(status='approved').count()
    rejected_registrations = Registration.objects.filter(status='rejected').count()
    
    # Get candidate status breakdown
    draft_candidates = Candidate.objects.filter(status='Draft').count()
    new_candidates = Candidate.objects.filter(status='New').count()
    approved_candidates = Candidate.objects.filter(status='Approved').count()
    rejected_candidates = Candidate.objects.filter(status='Rejected').count()
    
    # Add statistics to context
    context.update({
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_registrations': total_registrations,
        'total_programs': total_programs,
        'pending_registrations': pending_registrations,
        'approved_registrations': approved_registrations,
        'rejected_registrations': rejected_registrations,
        'draft_candidates': draft_candidates,
        'new_candidates': new_candidates,
        'approved_candidates': approved_candidates,
        'rejected_candidates': rejected_candidates,
    })
    
    return context


__all__ = [
    'admin_dashboard',
    'register_model_files',
    'get_uploaded_documents_display',
    'check_file_already_uploaded',
    'deactivate_file_record'
]
