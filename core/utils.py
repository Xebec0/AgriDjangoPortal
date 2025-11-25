from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User


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
    from core.models import Candidate, Registration, AgricultureProgram, Notification
    from django.db.models import Count, Q
    
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


def find_user_documents(user):
    """
    Scan all of a user's registrations to find previously uploaded documents
    Returns a dictionary of document types and their sources
    """
    from core.models import Registration, Candidate
    
    document_types = ['tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance', 'passport_scan']
    found_documents = {}
    
    # Get all registrations for this user
    registrations = Registration.objects.filter(user=user)
    
    # Search for each document type across all registrations
    for doc_type in document_types:
        for registration in registrations:
            doc = getattr(registration, doc_type, None)
            if doc:
                # Store the document along with metadata
                found_documents[doc_type] = {
                    'file': doc,
                    'source': f"Registration for {registration.program.title}",
                    'date': registration.registration_date,
                    'registration_id': registration.id
                }
                break  # Found a document of this type, no need to check further registrations
    
    return found_documents


def get_available_documents(candidate):
    """
    Get both existing candidate documents and other available documents from user's registrations
    Returns a dictionary of documents with their status (uploaded/available)
    """
    from core.models import Registration
    
    document_types = ['tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance', 'passport_scan']
    documents = {}
    
    # First check which documents are already uploaded to the candidate profile
    for doc_type in document_types:
        doc = getattr(candidate, doc_type, None)
        if doc:
            documents[doc_type] = {
                'status': 'uploaded',
                'file': doc,
                'source': 'Current profile',
                'date': candidate.updated_at
            }
        else:
            documents[doc_type] = {
                'status': 'not_uploaded',
                'file': None
            }
    
    # If the candidate has a created_by user, check their registrations for available documents
    if candidate.created_by:
        user_documents = find_user_documents(candidate.created_by)
        
        # Add available documents (only for types that aren't already uploaded)
        for doc_type, doc_info in user_documents.items():
            if documents.get(doc_type, {}).get('status') != 'uploaded':
                documents[doc_type] = {
                    'status': 'available',
                    'file': doc_info['file'],
                    'source': doc_info['source'],
                    'date': doc_info['date'],
                    'registration_id': doc_info['registration_id']
                }
    
    return documents


def import_document_to_candidate(candidate, doc_type, registration_id):
    """
    Import a document from a registration to a candidate
    """
    from core.models import Registration
    
    try:
        registration = Registration.objects.get(id=registration_id)
        doc = getattr(registration, doc_type, None)
        
        if doc:
            setattr(candidate, doc_type, doc)
            candidate.save(update_fields=[doc_type])
            return True
        return False
    except Registration.DoesNotExist:
        return False
