from django.db.models import Q
from django.utils import timezone

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
