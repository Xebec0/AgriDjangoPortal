# File Metadata Checker Bug Fix - COMPLETE

## Problems Identified

### Problem 1: Same Form Submission Validation
The file metadata checker was **not working** for detecting duplicates in the same form submission because it was checking for duplicate files using `hasattr(file_obj, 'read')`, which returns `True` for both:
1. **NEW uploaded files** (InMemoryUploadedFile/TemporaryUploadedFile) - what we want to validate
2. **EXISTING saved files** (FieldFile objects) - should be ignored during validation

### Problem 2: Previously Saved Files Validation  
The individual field validators (clean_tor(), clean_nbi_clearance(), etc.) were calling `validate_no_duplicate()` for ALL files, including existing saved files. This caused:
- False validations of existing files against themselves
- Missed duplicate checks for NEW files being uploaded to different fields

### Problem 3: Signal Re-registering ALL Files (CRITICAL BUG) ⚠️
**This was the main issue preventing duplicate detection from working!**

The `track_profile_files()` signal was re-registering ALL file fields on every save, not just newly uploaded ones. This caused:
1. User uploads file to TOR → saves → file registered with hash X ✓
2. User uploads SAME file to NC2 → saves → signal fires:
   - Re-registers TOR (deactivates old record, creates new one)
   - Registers NC2 (no active TOR record exists to compare against)
3. Result: Duplicate accepted because TOR record was deactivated ✗

**Root Cause**: `register_model_files()` was called on ALL fields every save, causing `register_upload()` to deactivate previous records (lines 542-546 in models.py)

## Root Causes

```python
# ISSUE 1 - Form-level validation (BROKEN):
if file_obj and hasattr(file_obj, 'read'):  # Matches BOTH new and existing files
    file_hash = UploadedFile.calculate_file_hash(file_obj)

# ISSUE 2 - Field-level validation (BROKEN):
def clean_nbi_clearance(self):
    nbi_clearance = self.cleaned_data.get('nbi_clearance')
    if nbi_clearance:  # Validates BOTH new and existing files
        validate_no_duplicate(self.instance.user, 'nbi_clearance', nbi_clearance)
```

## Solutions Applied

### Fix 1: Form-Level Validation (ProfileUpdateForm.clean())
Changed to use `not isinstance(file_obj, FieldFile)` to **only validate NEW file uploads**:

```python
# NEW CODE (FIXED):
from django.db.models.fields.files import FieldFile

if file_obj and hasattr(file_obj, 'chunks') and not isinstance(file_obj, FieldFile):
    file_hash = UploadedFile.calculate_file_hash(file_obj)
    # ... validation logic
```

### Fix 2: Field-Level Validation (All clean_* methods)
Added FieldFile check to only validate NEW uploads:

```python
# NEW CODE (FIXED):
def clean_nbi_clearance(self):
    from django.db.models.fields.files import FieldFile
    nbi_clearance = self.cleaned_data.get('nbi_clearance')
    if nbi_clearance:
        validate_file_size(nbi_clearance)
        validate_file_extension(nbi_clearance, ['.pdf', '.jpg', '.jpeg', '.png'])
        # Check for duplicates ONLY for NEW uploads
        if self.instance and self.instance.user and not isinstance(nbi_clearance, FieldFile):
            validate_no_duplicate(self.instance.user, 'nbi_clearance', nbi_clearance)
    return nbi_clearance
```

### Fix 3: Signal File Registration (CRITICAL FIX) ⚠️
Modified signal to only register files that actually changed:

```python
# NEW CODE (FIXED):
@receiver(post_save, sender=Profile)
def track_profile_files(sender, instance, created, **kwargs):
    if instance.user and instance.pk:
        document_fields = [...]
        
        for field_name in document_fields:
            current_file = getattr(instance, field_name, None)
            
            if current_file and hasattr(current_file, 'name') and current_file.name:
                # Check if this is a new or changed file
                existing_record = UploadedFile.objects.filter(
                    user=instance.user,
                    document_type=field_name,
                    is_active=True
                ).first()
                
                # Only register if file path changed
                if not existing_record or existing_record.file_path != current_file.name:
                    UploadedFile.register_upload(...)
```

**Key Changes:**
- Only registers files with changed file paths
- Prevents deactivation of existing file records
- Maintains active records for duplicate checking

## Files Modified

- `core/forms.py`:
  - Line 329: Fixed `ProfileUpdateForm.clean()` for same-submission duplicate detection
  - Lines 221-307: Fixed all `clean_*` methods (clean_license_scan, clean_passport_scan, clean_academic_certificate, clean_tor, clean_nc2_tesda, clean_diploma, clean_good_moral, clean_nbi_clearance)

- `core/signals.py`:
  - Lines 198-243: Fixed `track_profile_files()` signal to only register files that were actually uploaded/changed
  - **CRITICAL FIX**: Signal was re-registering ALL files on every save, deactivating existing records
  - Now checks if file path changed before registering

## How to Test the Fix

### Test Scenario 1: Same Form Submission Duplicates
1. Navigate to http://127.0.0.1:8000/profile/
2. Scroll to the "Required Documents" section
3. Upload **the same file** to BOTH:
   - **NC2 from TESDA** field
   - **Diploma** field
4. Click "Save Changes"

**Expected Result:**
```
✗ NC2 from TESDA: You uploaded the same file to both 'NC2 from TESDA' and 'Diploma'. 
  Each document must be unique. Please upload different files.

✗ Diploma: You uploaded the same file to both 'NC2 from TESDA' and 'Diploma'. 
  Each document must be unique. Please upload different files.
```
Form will **NOT submit** ✓

### Test Scenario 2: Previously Saved File Duplicates
1. Navigate to http://127.0.0.1:8000/profile/
2. Upload a file to **TOR (Transcript of Records)** field only
3. Click "Save Changes" - this should succeed ✓
4. Return to profile and upload **the same file** to **NBI Clearance** field
5. Click "Save Changes"

**Expected Result:**
```
✗ NBI Clearance: This file has already been uploaded as your Transcript of Records (TOR). 
  Each document must be unique. Please upload a different file.
```
Form will **NOT submit** ✓

## Additional Validation Features

The system now properly validates:
1. ✓ **Duplicate files within same form submission** (same file to multiple fields)
2. ✓ **Duplicate files across previous uploads** (file already uploaded to another field in past)
3. ✓ **File size** (max 5MB)
4. ✓ **File extensions** (PDF, JPG, JPEG, PNG only)

## Technical Details

The validation system uses a **two-layer approach**:

### Layer 1: Field-Level Validation (clean_* methods)
Each document field has its own `clean_*` method that:
1. Validates file size and extension
2. Checks if the file is a NEW upload (not an existing FieldFile)
3. Calls `validate_no_duplicate()` to check against **previously saved files** in the `UploadedFile` table
4. Raises `ValidationError` if duplicate found

**Example:**
```python
def clean_nbi_clearance(self):
    nbi_clearance = self.cleaned_data.get('nbi_clearance')
    if nbi_clearance and not isinstance(nbi_clearance, FieldFile):
        # Check against database for previously saved files
        validate_no_duplicate(self.instance.user, 'nbi_clearance', nbi_clearance)
    return nbi_clearance
```

### Layer 2: Form-Level Validation (clean() method)
The main `clean()` method checks for duplicates **within the same form submission**:
1. Collects all newly uploaded files from ALL fields
2. Calculates SHA-256 hash for each file
3. Compares hashes to detect duplicates in the same submission
4. Adds form errors if duplicates found on multiple fields
5. Prevents form submission until resolved

**Example:**
```python
def clean(self):
    file_hashes = {}
    for field_name in document_fields:
        file_obj = cleaned_data.get(field_name)
        if file_obj and not isinstance(file_obj, FieldFile):
            file_hash = UploadedFile.calculate_file_hash(file_obj)
            # Check if hash already seen in another field
            if file_hash in file_hashes.values():
                # Add errors to both fields
                ...
```

### File Registration System
After successful form save, Django signals automatically register files in the `UploadedFile` tracking table:
1. `post_save` signal fires for Profile model
2. `track_profile_files()` signal handler is called
3. `register_model_files()` registers all files with their hashes
4. Future uploads are checked against this table
