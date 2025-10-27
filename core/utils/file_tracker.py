"""
Utility functions for tracking and managing file uploads.
Ensures files are registered in the UploadedFile model for duplicate detection.
"""
from core.models import UploadedFile


def register_model_files(instance, user, model_name):
    """
    Register all file fields from a model instance in the UploadedFile tracking system.
    
    Args:
        instance: Model instance (Profile, Registration, or Candidate)
        user: User who owns/uploaded the files
        model_name: String name of the model ('Profile', 'Registration', 'Candidate')
    """
    # Define document fields for each model type
    document_fields = {
        'Profile': [
            'profile_image', 'license_scan', 'passport_scan', 'academic_certificate',
            'tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance'
        ],
        'Registration': [
            'tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance'
        ],
        'Candidate': [
            'passport_scan', 'tor', 'nc2_tesda', 'diploma', 'good_moral', 'nbi_clearance'
        ],
    }
    
    fields_to_check = document_fields.get(model_name, [])
    
    for field_name in fields_to_check:
        # Get the file field from the instance
        file_field = getattr(instance, field_name, None)
        
        # If file exists and has a name, register it
        if file_field and hasattr(file_field, 'name') and file_field.name:
            try:
                # Open the file to calculate hash
                file_field.open('rb')
                
                # Register the upload
                UploadedFile.register_upload(
                    user=user,
                    document_type=field_name,
                    file_obj=file_field,
                    model_name=model_name,
                    model_id=instance.pk
                )
                
                # Close the file
                file_field.close()
            except Exception as e:
                # Log error but don't fail the save operation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error registering file {field_name} for {model_name} {instance.pk}: {str(e)}")


def get_uploaded_documents_display(user):
    """
    Get a user-friendly display of all uploaded documents for a user.
    
    Returns a dictionary with document types as keys and file info as values.
    """
    uploaded_files = UploadedFile.get_user_documents(user, active_only=True)
    
    documents = {}
    for uploaded_file in uploaded_files:
        documents[uploaded_file.document_type] = {
            'name': uploaded_file.file_name,
            'size': uploaded_file.file_size,
            'uploaded_at': uploaded_file.uploaded_at,
            'display_name': uploaded_file.get_document_type_display(),
        }
    
    return documents


def check_file_already_uploaded(user, document_type, new_file):
    """
    Check if a file has already been uploaded by a user to a different document field.
    
    Returns:
        tuple: (is_duplicate, existing_document_type, error_message)
    """
    is_dup, existing, msg = UploadedFile.check_duplicate_upload(user, document_type, new_file)
    
    if is_dup and existing:
        return True, existing.get_document_type_display(), msg
    
    return False, None, None


def deactivate_file_record(user, document_type):
    """
    Mark a file record as inactive (when user deletes/replaces a document).
    """
    UploadedFile.objects.filter(
        user=user,
        document_type=document_type,
        is_active=True
    ).update(is_active=False)
