from django import template

register = template.Library()


@register.filter(name='file_exists')
def file_exists(file_field):
    """Check if a file field has an actual file that exists on the filesystem"""
    if not file_field:
        return False
    
    try:
        # Check if file_field has a name attribute and if the file exists
        if hasattr(file_field, 'name') and file_field.name:
            # Try to access the file's storage to check if it exists
            return file_field.storage.exists(file_field.name)
        return False
    except Exception:
        return False
