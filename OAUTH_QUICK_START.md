# OAuth 2.0 Implementation - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
Create/update `.env`:
```env
GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
FACEBOOK_OAUTH_CLIENT_ID=your_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_app_secret
MICROSOFT_OAUTH_CLIENT_ID=your_client_id
MICROSOFT_OAUTH_CLIENT_SECRET=your_client_secret
```

### Step 3: Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Run Server
```bash
python manage.py runsslserver
# Or:
python manage.py runserver
```

### Step 5: Test
Navigate to: `http://localhost:8000/register/social/`

---

## How It Works

### User Journey

```
Click Register
     ↓
/register/social/ (OAuth gateway)
     ↓
Select Provider (Google, Facebook, Microsoft, or Email)
     ↓
OAuth Provider Login
     ↓
Data Exchange & Redirect
     ↓
/register/ (pre-filled form)
     ↓
Complete Registration
     ↓
Account Created with OAuth Badge
```

### Pre-Filled Fields

When using OAuth, these fields are automatically populated:
- ✓ Email (read-only, verified)
- ✓ First Name (editable)
- ✓ Last Name (editable)  
- ✓ Profile Picture (downloaded and saved)

### Password Handling

- **OAuth Users**: Random password auto-generated (never shown)
- **Can Reset**: Users can set custom password anytime
- **Email Users**: Normal password entry required

---

## OAuth Provider Quick Setup

### Google
1. Create project: https://console.cloud.google.com/
2. Enable Google+ API
3. Create OAuth 2.0 Client ID (Web application)
4. Add redirect URI: `http://localhost:8000/auth/google/callback/`
5. Copy Client ID & Secret to `.env`

### Facebook
1. Create app: https://developers.facebook.com/
2. Add Facebook Login product
3. Configure OAuth redirect URIs
4. Add URI: `http://localhost:8000/auth/facebook/callback/`
5. Copy App ID & Secret to `.env`

### Microsoft
1. Register app: https://portal.azure.com/
2. Go to Azure AD → App registrations → New
3. Add redirect URI: `https://localhost:8000/auth/microsoft/callback/`
4. Create Client Secret
5. Copy Client ID & Secret to `.env`

---

## Key Files

| File | Purpose |
|------|---------|
| `core/oauth_utils.py` | OAuth token/data handling |
| `core/views.py` | OAuth views & registration |
| `core/urls.py` | OAuth routes |
| `core/models.py` | Profile OAuth fields |
| `templates/register-email.html` | OAuth provider selection UI |
| `templates/register.html` | Pre-filled registration form |

---

## Testing Endpoints

```bash
# Social login page
GET /register/social/

# OAuth callback (auto-generated redirect)
GET /auth/{provider}/callback/?code=...&state=...

# Registration form (pre-filled after OAuth)
GET /register/
POST /register/
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "OAuth not configured" | Check .env variables are set |
| "State mismatch" | Clear session/cookies, try again |
| "Email already exists" | User already has account |
| "Picture not saving" | Check media/ directory writable |
| Redirect URI mismatch | Verify exact match in OAuth settings |

---

## URLs

| Path | Purpose |
|------|---------|
| `/register/social/` | Social login gateway |
| `/register/` | Registration form |
| `/auth/{provider}/callback/` | OAuth callback |
| `/login/` | Login page |

---

## Features Implemented

✅ Google OAuth 2.0  
✅ Facebook OAuth 2.0  
✅ Microsoft OAuth 2.0  
✅ Email signup fallback  
✅ Auto-populate registration form  
✅ Profile picture download  
✅ Email verification auto-marked  
✅ Random password for OAuth users  
✅ OAuth metadata storage  
✅ CSRF protection  
✅ Error handling  
✅ Responsive design  
✅ Mobile friendly  

---

## Database Fields Added

```python
Profile.oauth_provider  # 'google', 'facebook', 'microsoft', 'email', null
Profile.oauth_id        # Provider's unique user ID
Profile.oauth_picture_url  # Original picture URL from provider
```

---

## Configuration Files Modified

1. **requirements.txt** - Added django-allauth, requests
2. **settings.py** - Added INSTALLED_APPS, SOCIALACCOUNT_PROVIDERS
3. **urls.py** - Added OAuth callback route
4. **models.py** - Added OAuth fields to Profile
5. **views.py** - Enhanced register(), added OAuth views
6. **register.html** - OAuth UI integration

---

## Next Steps

1. Deploy to production with HTTPS
2. Update redirect URIs in OAuth provider dashboards  
3. Set environment variables on production server
4. Run database migrations
5. Test OAuth flow end-to-end
6. Monitor logs for issues

---

## Performance Notes

- Profile picture downloads are non-blocking
- OAuth data stored temporarily in session only
- Access tokens not persisted
- No database queries for token validation
- Minimal impact on registration process

---

## Security Highlights

✓ State parameter validation (CSRF protection)  
✓ HTTPS required  
✓ No sensitive data stored in session  
✓ Random passwords for OAuth users  
✓ Email verification from provider trusted  
✓ Profile picture domain validation  

---

For detailed documentation, see: `OAUTH_INTEGRATION_GUIDE.md`
