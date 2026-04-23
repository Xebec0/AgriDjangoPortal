# Clear All Documents Feature

## Overview
Added a convenient "Clear All Documents" button to the Required Documents section in the user profile page. This allows users to quickly clear all uploaded documents with a single click instead of clearing them one by one.

## Features

### 1. Clear All Button
- Located in the Required Documents section header
- Red outline button with trash icon
- Opens a confirmation modal before clearing

### 2. Confirmation Modal
- **Warning message** explaining the action
- **List of documents** that will be cleared:
  - Transcript of Records (TOR)
  - NC2 from TESDA
  - Diploma
  - Good Moral Character
  - NBI Clearance
  - Passport Scan
  - Academic Certificate
- **Alert box** warning that action cannot be undone
- **Cancel** and **Confirm** buttons

### 3. Backend Processing
- Deletes physical files from storage
- Clears all document fields in the Profile model
- Deactivates file records in UploadedFile tracking system
- Shows success/error messages
- Creates notification for the user
- Logs any errors

## Files Modified

### 1. `templates/profile.html`
- **Line 565-572**: Added "Clear All Documents" button in section header
- **Lines 989-1029**: Added confirmation modal with warning and document list

### 2. `core/views.py`
- **Lines 472-523**: Added `clear_all_documents()` view function
  - Requires login (`@login_required`)
  - Requires POST method (`@require_POST`)
  - Deletes files and clears fields
  - Updates UploadedFile tracking system
  - Provides user feedback via messages and notifications

### 3. `core/urls.py`
- **Line 18**: Added URL route `profile/clear-documents/`

## How It Works

### User Flow
1. User navigates to their profile page
2. Scrolls to "Required Documents" section
3. Clicks "Clear All Documents" button
4. Modal appears with warning and document list
5. User clicks "Yes, Clear All Documents" to confirm (or Cancel to abort)
6. All documents are cleared
7. Success message appears
8. User is redirected back to profile page

### Technical Flow
```
User clicks button
    ↓
Modal opens (Bootstrap)
    ↓
User confirms
    ↓
POST request to /profile/clear-documents/
    ↓
clear_all_documents() view executes:
    - Gets user's profile
    - Iterates through document fields
    - Deletes physical files
    - Clears database fields
    - Deactivates UploadedFile records
    - Creates notification
    ↓
Redirects to profile page
    ↓
Success message displayed
```

## Security Features

1. **Login Required**: Only authenticated users can access
2. **POST Only**: Prevents accidental clearing via GET requests
3. **CSRF Protection**: Django CSRF token required
4. **User Isolation**: Only clears documents for the logged-in user
5. **Confirmation Modal**: Prevents accidental clicks

## Error Handling

- Graceful handling of missing files
- Logs warnings for file deletion errors
- Shows error message to user if operation fails
- Continues clearing other documents even if one fails

## Testing

### Test Scenario 1: Clear All Documents
1. Upload documents to multiple fields (TOR, NBI, Diploma, etc.)
2. Click "Clear All Documents" button
3. Verify modal appears with correct warning
4. Click "Yes, Clear All Documents"
5. Verify success message appears
6. Verify all document fields are empty
7. Verify physical files are deleted from storage

### Test Scenario 2: Cancel Operation
1. Click "Clear All Documents" button
2. Modal appears
3. Click "Cancel"
4. Verify modal closes
5. Verify no documents are cleared

### Test Scenario 3: Empty Documents
1. Ensure no documents are uploaded
2. Click "Clear All Documents" button
3. Confirm operation
4. Verify no errors occur
5. Verify success message still appears

## UI/UX Improvements

- **Visual Hierarchy**: Button positioned prominently but not intrusively
- **Color Coding**: Red color indicates destructive action
- **Icons**: Trash icon clearly indicates deletion
- **Confirmation**: Modal prevents accidental data loss
- **Feedback**: Success/error messages inform user of result
- **Notifications**: System notification created for user's records

## Future Enhancements

Possible improvements:
1. Add "Undo" functionality with temporary file retention
2. Show count of documents that will be cleared
3. Add option to selectively clear specific documents
4. Export documents before clearing
5. Add admin audit log for document clearing actions
