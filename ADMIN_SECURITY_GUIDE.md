# Admin Security Guide - Farm Images & Program Management

## 🔒 Security Overview

**CRITICAL**: Only administrators (superusers) can upload farm images and modify program display settings.

## 🛡️ Security Levels

### Level 1: Django Admin Access
**Required**: `is_staff = True`

**Can Access**:
- Admin panel at `/admin/`
- View agriculture programs
- View program details

**Cannot Do**:
- Upload or modify farm images (unless superuser)
- Change featured status (unless superuser)
- Delete programs (unless superuser)

### Level 2: Superuser (Administrator)
**Required**: `is_superuser = True`

**Full Access**:
- ✅ Upload farm images
- ✅ Change farm images
- ✅ Delete farm images
- ✅ Mark programs as featured
- ✅ Unmark programs as featured
- ✅ Delete programs
- ✅ All program management

## 🔐 Security Measures Implemented

### 1. **Admin Panel Protection**
```python
# Only staff can access admin
def has_change_permission(self, request, obj=None):
    return request.user.is_staff
```

### 2. **Image Upload Restriction**
```python
# Only superusers can modify images
def get_readonly_fields(self, request, obj=None):
    if not request.user.is_superuser:
        return ('image', 'is_featured')
    return ()
```

### 3. **Delete Protection**
```python
# Only superusers can delete programs
def has_delete_permission(self, request, obj=None):
    return request.user.is_superuser
```

### 4. **No Public Forms**
- ❌ No public forms expose AgricultureProgram model
- ❌ No views allow program image upload outside admin
- ❌ No API endpoints for image modification
- ✅ Only admin panel can modify programs

### 5. **Field-Level Security**
- Image field: **Superuser only**
- Is_featured field: **Superuser only**
- Display Settings section: **Collapsed by default**
- Warning message: **"⚠️ ADMIN ONLY"**

## 👥 User Permission Matrix

| Action | Regular User | Staff User | Superuser |
|--------|--------------|------------|-----------|
| View programs | ✅ | ✅ | ✅ |
| Apply to programs | ✅ | ✅ | ✅ |
| Access admin panel | ❌ | ✅ | ✅ |
| View program in admin | ❌ | ✅ | ✅ |
| Edit program details | ❌ | ✅ | ✅ |
| **Upload farm images** | ❌ | ❌ | ✅ |
| **Change images** | ❌ | ❌ | ✅ |
| **Mark as featured** | ❌ | ❌ | ✅ |
| Delete programs | ❌ | ❌ | ✅ |

## 🚨 Important Security Notes

### 1. Creating Superusers
Only create superuser accounts for trusted administrators:

```bash
python manage.py createsuperuser
# Enter username, email, and password
```

### 2. Staff vs Superuser
- **Staff**: Can view admin, edit basic program info
- **Superuser**: Full control including images and featured status

### 3. Media File Access
- Uploaded images stored in `media/program_images/`
- Files served by Django in development
- In production, configure web server (Nginx/Apache) with proper permissions

### 4. Audit Trail
All image uploads and modifications are logged in:
- Django admin logs
- Activity logs (if enabled)
- Server access logs

## 🔍 Verification Checklist

### For Administrators:
- [ ] Only trusted users have superuser status
- [ ] Staff users cannot modify images (verified)
- [ ] Regular users have no admin access
- [ ] Image upload directory has proper permissions
- [ ] Production media files are secure

### For Developers:
- [ ] No public forms expose program images
- [ ] No views allow image upload outside admin
- [ ] Admin permissions properly configured
- [ ] get_readonly_fields() enforced for non-superusers
- [ ] has_delete_permission() restricted to superusers

## 🛠️ How to Grant Image Upload Permission

### Option 1: Make User a Superuser (Recommended)
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='username_here')
user.is_superuser = True
user.is_staff = True
user.save()
```

### Option 2: Via Admin Panel
1. Log in as superuser
2. Go to `/admin/auth/user/`
3. Select the user
4. Check both:
   - ✅ Staff status
   - ✅ Superuser status
5. Save

### Option 3: During User Creation
```bash
python manage.py createsuperuser
```

## 🚫 What Regular Staff Users See

When a staff user (non-superuser) opens a program in admin:

1. **Display Settings Section**: 
   - Collapsed by default
   - Shows: "⚠️ ADMIN ONLY: Only administrators can modify these settings"
   - Image field: **Read-only** (cannot upload/change)
   - Is_featured field: **Read-only** (cannot check/uncheck)

2. **Other Fields**:
   - Title, description: Editable ✅
   - Location, dates: Editable ✅
   - Capacity: Editable ✅
   - Requirements: Editable ✅

3. **Actions**:
   - Can save basic program info ✅
   - Cannot upload images ❌
   - Cannot change featured status ❌
   - Cannot delete program ❌

## 🔒 Production Security Best Practices

### 1. File Upload Security
```python
# In settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']
```

### 2. Media File Permissions
```bash
# Set proper permissions
chmod 755 media/
chmod 644 media/program_images/*
```

### 3. Web Server Configuration
**Nginx Example**:
```nginx
location /media/ {
    alias /path/to/media/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 4. HTTPS Enforcement
- Always use HTTPS in production
- Secure admin panel with SSL
- Enable CSRF protection (already enabled)

## 📊 Monitoring & Auditing

### Check Who Has Superuser Access:
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    print(f"{user.username} - {user.email}")
```

### Review Recent Image Uploads:
```bash
ls -lht media/program_images/ | head -20
```

### Check Admin Activity:
1. Go to `/admin/`
2. Click "Log entries" (if available)
3. Filter by action: "Changed" + "image"

## ⚠️ Security Warnings

### DON'T:
- ❌ Give superuser status to untrusted users
- ❌ Share superuser credentials
- ❌ Allow anonymous image uploads
- ❌ Disable CSRF protection
- ❌ Expose admin panel without HTTPS

### DO:
- ✅ Regularly audit superuser accounts
- ✅ Use strong passwords for admin accounts
- ✅ Enable two-factor authentication (if available)
- ✅ Monitor image upload activity
- ✅ Keep Django and dependencies updated
- ✅ Regular security audits

## 🧪 Testing Security

### Test 1: Non-superuser Cannot Upload Images
```python
# Login as staff user (not superuser)
# Try to edit program
# Verify: Image field is read-only
```

### Test 2: Regular User Cannot Access Admin
```python
# Login as regular user
# Try to access /admin/
# Verify: Redirected to login or 403 error
```

### Test 3: Only Superuser Can Delete
```python
# Login as staff user (not superuser)
# Try to delete program
# Verify: Delete button not available
```

## 📝 Compliance Notes

### Data Protection:
- Image uploads are logged
- Only authorized personnel can modify images
- Regular security audits recommended
- Access controls enforced at multiple levels

### GDPR Considerations:
- Admin actions are traceable
- Image deletion removes files from server
- User access is role-based
- Audit logs maintain compliance

## 🆘 Troubleshooting

### Issue: Staff user can upload images
**Solution**: 
1. Verify user is NOT superuser
2. Check `get_readonly_fields()` method in admin.py
3. Clear browser cache and reload

### Issue: Superuser cannot upload images
**Solution**:
1. Verify user.is_superuser = True
2. Check media directory permissions
3. Verify MEDIA_ROOT and MEDIA_URL settings

### Issue: Images not showing after upload
**Solution**:
1. Check file permissions in media/program_images/
2. Verify web server serves media files correctly
3. Run `python manage.py collectstatic` if needed

## 📞 Support

For security concerns or issues:
1. Check this guide first
2. Review Django admin logs
3. Check server error logs
4. Contact system administrator

---

**Last Updated**: 2025-10-03  
**Security Level**: High  
**Status**: ✅ Active and Enforced
