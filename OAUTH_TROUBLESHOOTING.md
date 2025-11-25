# OAuth 2.0 - Quick Troubleshooting Guide

## 🔴 Red Light Issues (Critical)

### OAuth button shows "OAuth X is not configured"

**Problem**: OAuth provider credentials not set  
**Solution**:
1. Check `.env` file has all credentials
2. Verify variable names are EXACTLY:
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `GOOGLE_OAUTH_CLIENT_SECRET`
   - `FACEBOOK_OAUTH_CLIENT_ID`
   - `FACEBOOK_OAUTH_CLIENT_SECRET`
   - `MICROSOFT_OAUTH_CLIENT_ID`
   - `MICROSOFT_OAUTH_CLIENT_SECRET`
3. Restart Django server: `python manage.py runserver`
4. Reload browser page

---

### OAuth flow shows "State mismatch" error

**Problem**: Session-based state validation failed  
**Solution**:
1. Clear browser cookies for localhost
2. Clear browser cache
3. Open in private/incognito window
4. Try again
5. If persists, check Django session backend

---

### "Email already registered" error during OAuth

**Problem**: Email exists in system from different provider  
**Solution**:
- Option 1: Use different email for OAuth
- Option 2: Delete existing account (admin panel)
- Option 3: Merge accounts (feature in v2.0)

---

## 🟡 Yellow Light Issues (Important)

### Profile picture not downloading

**Problem**: Image from provider not saved  
**Solution**:
1. Check `media/` directory exists and is writable
   ```bash
   ls -la media/
   chmod 755 media/
   ```
2. Check picture URL is valid (test in browser)
3. Check network connectivity
4. Check Django logs: `error.log`
5. Picture URL saved as backup in `profile.oauth_picture_url`

---

### OAuth provider shows "Invalid Redirect URI"

**Problem**: Redirect URL doesn't match provider settings  
**Solution**:
1. Check provider settings exactly match:
   - Domain (localhost vs 127.0.0.1)
   - Protocol (http vs https)
   - Port (8000, 8080, etc.)
   - Path (`/auth/{provider}/callback/`)
2. Examples:
   - Local: `http://localhost:8000/auth/google/callback/`
   - Production: `https://yourdomain.com/auth/google/callback/`

---

### OAuth provider returns error during login

**Problem**: User denied permissions or provider error  
**Solution**:
1. User declined permissions → Try again, grant permissions
2. Provider temporarily down → Try different provider
3. Check provider status page
4. Check Django logs for error details
5. Retry in fresh browser session

---

### Form not pre-filled with OAuth data

**Problem**: Email/name/picture not showing after OAuth  
**Solution**:
1. Check Django session working: `python manage.py shell` → test session
2. Check OAuth data stored: Add debug print in `views.py`
3. Check template context: Verify `oauth_data` passed
4. Check browser session not cleared
5. Verify form initialization code

---

## 🟢 Green Light Issues (Minor)

### OAuth callback too slow

**Problem**: Takes >2 seconds to return to registration  
**Solution**:
- This is normal for profile picture download
- Picture download is non-blocking
- User can proceed without waiting
- Check network speed with: `curl -I https://api.provider.com`

---

### Profile picture quality poor

**Problem**: Downloaded image appears blurry  
**Solution**:
- Providers may limit image resolution
- User can upload better picture in profile
- Check provider's returned image size
- Facebook/Google may use different sizes

---

### OAuth ID already exists error

**Problem**: Duplicate OAuth account attempted  
**Solution**:
1. OAuth ID is unique (one per provider per user)
2. Same user can't create two accounts with same provider
3. If needed to reset: Delete profile from admin panel
4. User can use different provider instead

---

## 🔧 Debugging Steps

### Check Django Logs
```bash
tail -f error.log
tail -f debug.log
```

### Test OAuth Directly
```python
python manage.py shell
from core.oauth_utils import OAuthDataExtractor
# Test with real access token
data = OAuthDataExtractor.get_google_user_data('your_access_token')
print(data)
```

### Check Database
```python
python manage.py shell
from django.contrib.auth.models import User
from core.models import Profile

# Check user created
user = User.objects.get(username='testuser')
profile = Profile.objects.get(user=user)

# Check OAuth fields
print(f"Provider: {profile.oauth_provider}")
print(f"OAuth ID: {profile.oauth_id}")
print(f"Email Verified: {profile.email_verified}")
print(f"Picture URL: {profile.oauth_picture_url}")
```

### Check Session Data
```python
# In view
print(request.session.get('oauth_data'))
```

### Test OAuth URL
```bash
# Test Google OAuth endpoint
curl "https://www.googleapis.com/oauth2/v1/userinfo?access_token=YOUR_TOKEN"

# Test Facebook endpoint
curl "https://graph.facebook.com/me?access_token=YOUR_TOKEN&fields=id,email,name"

# Test Microsoft endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://graph.microsoft.com/v1.0/me"
```

---

## 📋 Pre-OAuth Verification Checklist

Before testing, verify:

- [ ] `.env` file exists in project root
- [ ] All OAuth credentials set in `.env`
- [ ] Django server restarted after `.env` changes
- [ ] Media directory exists and writable: `media/`
- [ ] Database migrated: `python manage.py migrate`
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] HTTPS working (or using localhost:8000)
- [ ] Redirect URIs match exactly in provider settings

---

## 🔍 Provider-Specific Debugging

### Google OAuth Issues

**Check Google Credentials**:
```bash
# Verify client ID format
# Should be: xxxxx.apps.googleusercontent.com

# Test token endpoint
curl -X POST https://oauth2.googleapis.com/token \
  -d "code=AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "grant_type=authorization_code"
```

**Google Console**:
- Project → APIs & Services → Credentials
- Check OAuth 2.0 Client ID (Web application)
- Verify Authorized JavaScript origins: `http://localhost:8000`
- Verify Authorized redirect URIs: `http://localhost:8000/auth/google/callback/`

---

### Facebook OAuth Issues

**Check Facebook Credentials**:
```bash
# Test token endpoint
curl "https://graph.facebook.com/v15.0/oauth/access_token" \
  -d "code=AUTH_CODE" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI"
```

**Facebook Settings**:
- App Dashboard → Settings → Basic
- Check App ID and App Secret
- Product: Facebook Login → Settings
- Valid OAuth Redirect URIs: `http://localhost:8000/auth/facebook/callback/`

---

### Microsoft OAuth Issues

**Check Microsoft Credentials**:
```bash
# Test token endpoint
curl -X POST https://login.microsoftonline.com/common/oauth2/v2.0/token \
  -d "code=AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "grant_type=authorization_code" \
  -d "scope=https://graph.microsoft.com/.default"
```

**Azure Portal**:
- App registrations → Your App
- Check Application (client) ID
- Certificates & secrets → Client Secret
- Authentication → Redirect URIs: `https://yourdomain.com/auth/microsoft/callback/`

---

## 🚨 Emergency Procedures

### If OAuth Flow Breaks Production

1. **Immediate Action**:
   - Users can still use email signup
   - OAuth users can reset password
   - System continues functioning

2. **Disable Specific Provider**:
   ```python
   # In settings.py - temporarily
   SOCIALACCOUNT_PROVIDERS = {
       # Remove problematic provider
   }
   ```

3. **Check and Fix**:
   - Verify OAuth credentials still valid
   - Check provider status page
   - Update redirect URIs if changed
   - Restart Django server

4. **Rollback if Needed**:
   - Revert last commit
   - Verify no data loss
   - Continue with email signup only

---

## 📞 Getting Help

### Check These First
1. ✅ Read OAUTH_INTEGRATION_GUIDE.md
2. ✅ Check error.log for details
3. ✅ Verify .env variables
4. ✅ Test in incognito window
5. ✅ Restart Django server

### Documentation
- Full Guide: `OAUTH_INTEGRATION_GUIDE.md`
- Quick Start: `OAUTH_QUICK_START.md`
- Debugging: This file

### Common Solutions
- "Not configured" → Check .env
- "State mismatch" → Clear cookies
- "Already registered" → Different email
- "No picture" → Check media/ permissions
- "Slow redirect" → Normal (background download)

---

## 💡 Tips & Tricks

### Test Without Real OAuth
```python
# In views.py - add debug code
oauth_data = {
    'provider': 'google',
    'oauth_id': 'test123',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'picture': None,
    'email_verified': True,
}
store_oauth_session_data(request, oauth_data)
return redirect('register')
```

### Test Image Download
```python
from core.oauth_utils import ProfilePictureDownloader
from core.models import Profile

profile = Profile.objects.first()
url = "https://www.gravatar.com/avatar/...?s=200"
result = ProfilePictureDownloader.download_and_save_picture(
    profile, url, 'test'
)
print(f"Success: {result}")
```

### Monitor Performance
```bash
# Watch for slow requests
watch -n 1 'tail error.log | grep "Completed in"'
```

---

## ✅ Success Indicators

If you see these, OAuth is working:

✅ OAuth buttons appear on `/register/social/`  
✅ Clicking button redirects to provider  
✅ Provider shows login screen  
✅ Redirects back to `/register/`  
✅ Form shows pre-filled email  
✅ Verification badge visible  
✅ Profile picture shows (if available)  
✅ Account created successfully  
✅ Can log in with email  
✅ Profile shows oauth_provider value  

---

## 🎯 One-Minute Fix Guide

| Error | Fix |
|-------|-----|
| "Not configured" | Restart server after .env changes |
| "State mismatch" | Clear cookies in private window |
| "Redirect URI" | Match provider settings exactly |
| "Email exists" | Use different email or delete old |
| "No picture" | Check media/ directory writable |
| "Timeout" | Normal for background download |
| "Provider error" | Check provider status page |

---

**Last Updated**: November 26, 2025  
**Version**: 1.0

For detailed information, see: `OAUTH_INTEGRATION_GUIDE.md`
