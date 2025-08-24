# Form Simplification Summary - Agrostudies Registration System

## Changes Implemented

### 1. **Passport Fields - Hidden for Future Use**
- **Status**: ✅ Completed
- **Location**: `core/forms.py` - CandidateForm
- **Changes**:
  - Removed `passport_number` and `confirm_passport` fields from form display
  - Removed passport validation from clean() method
  - Passport fields will be set to empty/default values in the backend
  - Fields remain in database model for future activation

### 2. **University Field - Removed**
- **Status**: ✅ Completed  
- **Location**: `core/forms.py` and `core/views.py`
- **Changes**:
  - Removed university field from CandidateForm
  - Auto-creates "Not Specified" university entry in views.py
  - Removed university filter from CandidateSearchForm

### 3. **Document Upload Fields - Hidden**
- **Status**: ✅ Completed
- **Location**: `core/forms.py` - CandidateForm
- **Changes**:
  - Removed all document upload fields (tor, nc2_tesda, diploma, good_moral, nbi_clearance)
  - Kept document validation methods for potential future use

### 4. **Additional Info Fields - Removed**
- **Status**: ✅ Completed
- **Location**: `core/forms.py` - CandidateForm  
- **Changes**:
  - Removed: father_name, mother_name, religion, shoes_size, shirt_size, secondary_specialization, year_graduated, smokes
  - Removed: passport_issue_date, passport_expiry_date

### 5. **Welcome Message - Updated**
- **Status**: ✅ Completed
- **Location**: `templates/index.html` and `templates/base.html`
- **Changes**:
  - Updated to: "Welcome to Agrostudies Registration System for Farm Selection"
  - Updated footer text and all branding references

## Fields Remaining in Application Form

The simplified application form now only contains:
1. **First Name** (with confirmation)
2. **Last Name** (with confirmation)  
3. **Date of Birth**
4. **Country of Birth**
5. **Nationality**
6. **Gender**
7. **Specialization** (Agricultural field)
8. **Email**

## Backend Handling

In `core/views.py` - `apply_candidate()` function:
- Auto-creates "Not Specified" university if not exists
- Sets passport_number to empty string if not provided
- Sets default passport dates (1 year validity from today)
- Handles all other removed fields with defaults (empty/None)

## Testing Recommendations

1. **Test Application Flow**:
   - Navigate to `/programs/1/apply/`
   - Verify form displays only the simplified fields
   - Submit form without passport information
   - Confirm successful submission

2. **Test Data Integrity**:
   - Check that candidates are created with default values
   - Verify "Not Specified" university is created
   - Confirm passport fields are empty but don't cause errors

3. **Test Admin Functions**:
   - Verify candidate list displays correctly
   - Check export functions work with missing data
   - Ensure search/filter functions work without university field

## Future Activation

To re-enable passport fields in the future:
1. Add passport fields back to CandidateForm fields list
2. Re-add passport validation in clean() method
3. Update views.py to handle passport data properly
4. No database migration needed (fields still exist in model)

## Notes

- All changes are backward compatible
- Existing data is preserved
- System can handle both old (with passport) and new (without passport) records
- Document upload capability preserved in backend for future use
