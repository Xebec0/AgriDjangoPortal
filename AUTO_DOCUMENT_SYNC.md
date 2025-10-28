# Automatic Document Sync - Profile to Candidate

## Feature Overview

**Automatic Real-Time Document Synchronization**

When a user updates documents in their profile, the changes automatically sync to ALL their candidate records. This ensures consistency across the system.

## How It Works

### Trigger: Profile Save

Whenever a Profile is saved (created or updated), a Django signal automatically:
1. Finds all Candidate records created by that user
2. Syncs document changes from Profile → Candidate
3. Handles additions, updates, and deletions

### Signal Implementation

**File**: `core/signals.py`

```python
@receiver(post_save, sender=Profile)
def sync_profile_documents_to_candidates(sender, instance, created, **kwargs):
    """
    Automatically sync documents from Profile to all associated Candidate records.
    When user updates their profile documents, all their candidate applications get updated.
    """
```

## Document Mapping

| Profile Field | Candidate Field | Notes |
|--------------|----------------|-------|
| `passport_scan` | `passport_scan` | Direct mapping |
| `tor` | `tor` | Direct mapping |
| `nc2_tesda` | `nc2_tesda` | Direct mapping |
| `diploma` | `diploma` | Direct mapping |
| `academic_certificate` | `diploma` | Maps to same field |
| `good_moral` | `good_moral` | Direct mapping |
| `nbi_clearance` | `nbi_clearance` | Direct mapping |

## Use Cases

### 1. User Adds New Document ✅

**Scenario**: User uploads TOR to profile

```
User Action:
  Profile: TOR = documents/tor/transcript.pdf
  
Automatic Sync:
  Candidate #8: TOR = documents/tor/transcript.pdf ✓
  Candidate #12: TOR = documents/tor/transcript.pdf ✓
  
Result: All candidates updated instantly
```

### 2. User Replaces Document ✅

**Scenario**: User uploads new passport scan

```
User Action:
  Profile: passport_scan = new_passport.pdf (replaces old)
  
Automatic Sync:
  All candidates: passport_scan = new_passport.pdf ✓
  
Result: New file synced to all candidate records
```

### 3. User Removes Document ✅

**Scenario**: User deletes NBI clearance from profile

```
User Action:
  Profile: nbi_clearance = None (removed)
  
Automatic Sync:
  All candidates: nbi_clearance = None ✓
  
Result: Document removed from all candidate records
```

### 4. User Edits Profile (Any Field) ✅

**Scenario**: User updates name, phone, or any profile field

```
User Action:
  Profile.save() called (even if no document change)
  
Automatic Sync:
  System checks all documents
  Syncs any mismatches
  
Result: Ensures consistency on every profile update
```

## Sync Logic

### When Documents are Synced

```python
# Profile has file, Candidate doesn't
Profile: document.pdf
Candidate: None
→ Copy to candidate ✓

# Profile has file, Candidate has different file
Profile: new_document.pdf
Candidate: old_document.pdf
→ Update candidate ✓

# Profile file removed, Candidate still has it
Profile: None
Candidate: old_document.pdf
→ Remove from candidate ✓

# Both have same file
Profile: document.pdf
Candidate: document.pdf
→ No change needed ✓
```

## Technical Details

### Signal Execution

1. **Trigger**: `post_save` signal on Profile model
2. **Timing**: After profile save completes
3. **Scope**: All candidates created by profile owner
4. **Logging**: INFO level for successful syncs

### Performance

- **Efficient**: Only updates candidates that need changes
- **Batch-aware**: Updates multiple candidates in one operation
- **Safe**: Exception handling prevents save failures

### Logging

```python
# Success logs
INFO: Synced tor from profile to candidate 8
INFO: Synced documents from profile 32 to 2 candidate(s)

# Removal logs
INFO: Removed diploma from candidate 8 (removed from profile)

# Error logs (if any)
ERROR: Error syncing Profile documents to Candidates for user...
```

## Testing

### Test Scenario 1: Manual Update

```python
# Get user and profile
user = User.objects.get(username='arvsshirahama')
profile = user.profile

# Update a document in profile
# (Upload through Django admin or web form)

# Trigger sync manually if needed
profile.save()

# Verify sync
candidate = Candidate.objects.get(created_by=user)
assert candidate.tor == profile.tor  # Should match ✓
```

### Test Scenario 2: Web Form Update

```
1. Visit: http://127.0.0.1:8000/profile/
2. Click "Edit Profile"
3. Upload new TOR document
4. Click "Save Changes"
5. Visit: http://127.0.0.1:8000/candidates/8/edit/
6. Verify: TOR is updated ✓
```

### Test Scenario 3: Delete Document

```
1. Visit: http://127.0.0.1:8000/profile/
2. Check "Remove current document" for NBI Clearance
3. Click "Save Changes"
4. Visit: http://127.0.0.1:8000/candidates/8/edit/
5. Verify: NBI Clearance removed ✓
```

## Verification

### Check Sync Status

```python
from core.models import User, Candidate

user = User.objects.get(username='username')
profile = user.profile
candidates = Candidate.objects.filter(created_by=user)

for candidate in candidates:
    print(f"Candidate {candidate.id}:")
    print(f"  TOR matches: {candidate.tor == profile.tor}")
    print(f"  Diploma matches: {candidate.diploma == profile.diploma}")
    # ... check other documents
```

### Force Sync

If documents are out of sync, trigger sync manually:

```python
user = User.objects.get(username='username')
profile = user.profile
profile.save()  # Triggers sync signal
```

## Benefits

### ✅ For Users
- **Upload once**: Documents in profile automatically appear in applications
- **Update once**: Changes reflect everywhere instantly
- **Consistent data**: No confusion about which documents are current

### ✅ For Staff
- **Accurate records**: Candidate documents always match profile
- **Less manual work**: No need to manually update candidate documents
- **Reliable data**: Automatic sync prevents outdated information

### ✅ For System
- **Data integrity**: Single source of truth (profile)
- **Real-time updates**: Changes propagate immediately
- **Audit trail**: Logging tracks all syncs

## Edge Cases Handled

### Multiple Candidates

```
User has 3 candidate records:
  Candidate #8 (Program A)
  Candidate #12 (Program B)
  Candidate #15 (Program C)

User updates profile documents:
→ All 3 candidates get updated ✓
```

### New Applications

```
User updates profile → applies to program:
→ New candidate created with latest documents ✓
→ Already synced (uses latest profile data)
```

### Academic Certificate vs Diploma

```
Profile has both:
  academic_certificate = cert.pdf
  diploma = diploma.pdf

Sync logic:
  If candidate.diploma already set → don't override with academic_certificate
  If candidate.diploma empty → use academic_certificate
  
→ Prevents accidental overwrites ✓
```

## File Operations

### What Gets Synced

✅ File references (paths in database)  
✅ File field updates  
✅ File removals (set to None)  

### What Doesn't Get Synced

❌ Actual file copying (not needed - uses same storage)  
❌ File metadata changes  
❌ Profile fields other than documents  

## Monitoring

### Check Logs

```bash
# In Django logs, look for:
INFO: Synced tor from profile to candidate 8
INFO: Removed diploma from candidate 8
ERROR: Error syncing Profile documents to Candidates
```

### Admin Interface

No special admin interface needed - sync happens automatically in background.

## Troubleshooting

### Documents Not Syncing?

**Possible Causes**:
1. Profile save not triggering (check signals are enabled)
2. No candidates for user (nothing to sync to)
3. Error in sync logic (check logs)

**Solution**:
```python
# Force sync
user = User.objects.get(username='username')
profile = user.profile
profile.save()
```

### Old Documents Still Showing?

**Cause**: Browser cache or page not refreshed

**Solution**:
1. Hard refresh candidate page (Ctrl+F5)
2. Clear browser cache
3. Check database directly to confirm

## Implementation Details

### Files Modified

| File | Changes |
|------|---------|
| `core/signals.py` | ✅ Added `sync_profile_documents_to_candidates` signal |

### Dependencies

- Django signals framework
- Profile and Candidate models
- Python logging

### Performance Impact

- **Minimal**: Only runs when profile is saved
- **Efficient**: Skips unchanged documents
- **Async-ready**: Can be moved to Celery task if needed

---

## Summary

**Feature**: Automatic document sync from Profile to Candidate  
**Trigger**: Profile save event  
**Scope**: All documents for all candidates of user  
**Actions**: Add, update, remove documents  
**Status**: ✅ **ACTIVE AND WORKING**  

---

## Real-World Example

### User Journey

1. **User uploads documents in profile**
   - TOR, Diploma, NBI Clearance, etc.

2. **User applies to Program A**
   - Candidate #8 created with all documents ✓

3. **User uploads new NBI clearance (renewal)**
   - Profile updated
   - Signal triggers
   - Candidate #8 automatically updated ✓

4. **User applies to Program B**
   - Candidate #15 created with latest documents ✓

5. **User removes old diploma**
   - Profile updated
   - Both candidates updated ✓

**Result**: All candidate records always have current documents!

---

**The automatic sync is now active. Any profile document change will instantly reflect in all candidate records!** 🎉
