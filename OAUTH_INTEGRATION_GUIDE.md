# OAuth 2.0 Social Authentication Integration Guide

## Overview

This document provides complete setup instructions and testing procedures for the OAuth 2.0 social authentication feature integrated into AgroStudies. The system now supports Google, Facebook, and Microsoft authentication providers with automatic profile pre-population.

## Architecture

### Updated User Flow

```
1. User clicks "Register" → Redirected to /register/social/
   ↓
2. Social Login Selection Page (register-email.html)
   - Google OAuth button
   - Facebook OAuth button  
   - Microsoft OAuth button
   - Email signup fallback
   ↓
3. User selects provider → OAuth provider login
   ↓
4. Provider redirects to /auth/{provider}/callback/
   ↓
5. Backend exchanges code for access token
   ↓
6. Backend retrieves user data from provider
   ↓
7. Data stored in session: oauth_data = {
       'provider': 'google',
       'oauth_id': '1234567890',
       'email': 'user@gmail.com',
       'first_name': 'John',
       'last_name': 'Doe',
       'picture': 'https://...',
       'email_verified': True
   }
   ↓
8. Redirect to /register/ with pre-filled form
   ↓
9. User completes registration with pre-filled data
   ↓
10. Account created with OAuth metadata saved
```

## Setup Instructions

### Step 1: Install Dependencies

The required packages have been added to `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key packages:
- `django-allauth>=0.52.0` - OAuth management
- `requests>=2.31.0` - API requests to OAuth providers

### Step 2: Configure Django Settings

Settings have been updated in `agrostudies_project/settings.py`:

```python
# INSTALLED_APPS includes:
- 'django.contrib.sites'
- 'allauth'
- 'allauth.account'
- 'allauth.socialaccount'
- 'allauth.socialaccount.providers.google'
- 'allauth.socialaccount.providers.facebook'
- 'allauth.socialaccount.providers.microsoft'

SITE_ID = 1

# OAuth Providers configured in SOCIALACCOUNT_PROVIDERS
```

### Step 3: Set Environment Variables

Create or update your `.env` file with OAuth provider credentials:

```env
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

# Facebook OAuth
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret

# Microsoft OAuth
MICROSOFT_OAUTH_CLIENT_ID=your_microsoft_client_id
MICROSOFT_OAUTH_CLIENT_SECRET=your_microsoft_client_secret
```

### Step 4: Create Database Migration

The Profile model has been updated with OAuth fields:

```python
# New fields in Profile model:
- oauth_provider: CharField (google, facebook, microsoft, email)
- oauth_id: CharField (unique provider ID)
- oauth_picture_url: URLField (original picture URL)
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Run Django Development Server

```bash
python manage.py runserver
```

Or with HTTPS (for OAuth):

```bash
python manage.py runsslserver 0.0.0.0:8000
```

---

## OAuth Provider Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google+ API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
5. Choose **Web application**
6. Add **Authorized redirect URIs**:
   - `http://localhost:8000/auth/google/callback/`
   - `https://yourdomain.com/auth/google/callback/` (production)
7. Copy **Client ID** and **Client Secret** to `.env`

### Facebook OAuth Setup

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create or select an App
3. Go to **Settings** → **Basic**
4. Copy **App ID** and **App Secret**
5. Go to **Facebook Login** → **Settings**
6. Add **Redirect URIs**:
   - `http://localhost:8000/auth/facebook/callback/`
   - `https://yourdomain.com/auth/facebook/callback/` (production)
7. Copy credentials to `.env`

### Microsoft OAuth Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Name: "AgroStudies"
5. Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
6. Redirect URI: `https://yourdomain.com/auth/microsoft/callback/`
7. Go to **Certificates & secrets**
8. Create a new **Client secret**
9. Copy **Application (client) ID** and **Client secret value**
10. Add to `.env`

---

## File Structure

### New Files

```
core/
├── oauth_utils.py          # OAuth utilities (token exchange, data extraction)
└── views.py                # Updated with OAuth views

templates/
└── register-email.html     # Social authentication gateway

migrations/
└── XXXX_add_oauth_fields.py  # Profile model updates
```

### Modified Files

```
core/
├── models.py               # Added OAuth fields to Profile
├── urls.py                 # Added OAuth callback routes
└── views.py                # Enhanced register view with OAuth support

settings.py                 # Django-allauth configuration

templates/
└── register.html           # OAuth pre-fill integration
```

---

## Key Components

### OAuth Utilities (`core/oauth_utils.py`)

#### OAuthDataExtractor
- `get_google_user_data(access_token)` - Fetch Google profile
- `get_facebook_user_data(access_token)` - Fetch Facebook profile
- `get_microsoft_user_data(access_token)` - Fetch Microsoft profile

#### OAuthTokenExchanger
- `exchange_google_code(code, redirect_uri)` - Google token exchange
- `exchange_facebook_code(code, redirect_uri)` - Facebook token exchange
- `exchange_microsoft_code(code, redirect_uri)` - Microsoft token exchange

#### ProfilePictureDownloader
- `download_and_save_picture(profile, picture_url, provider)` - Download and save OAuth profile picture

#### Session Management
- `store_oauth_session_data(request, oauth_data)` - Store in session
- `get_oauth_session_data(request)` - Retrieve from session
- `clear_oauth_session_data(request)` - Clear after registration

### URLs

```python
path('register/social/', views.social_register, name='social_register')
path('auth/<str:provider>/callback/', views.oauth_callback_get, name='oauth_callback')
```

### Views

#### social_register(request)
- Displays OAuth provider selection page
- Passes OAuth client IDs to template

#### oauth_callback_get(request, provider)
- Handles OAuth provider callback
- Exchanges authorization code for access token
- Retrieves user data from provider
- Stores data in session
- Redirects to registration form

#### register(request)
- Enhanced with OAuth detection
- Pre-fills form with OAuth data
- Sets read-only email field for OAuth users
- Auto-generates password for OAuth users
- Downloads profile picture
- Saves OAuth metadata to Profile model

---

## Testing Checklist

### Pre-Testing Setup

- [ ] Environment variables configured with valid OAuth credentials
- [ ] Database migrations applied
- [ ] Django development server running
- [ ] Redirect URIs configured in OAuth provider settings

### Test Case 1: Social Register Page Display

**Objective**: Verify social login selection page renders correctly

```
1. Navigate to http://localhost:8000/register/social/
2. Verify page displays:
   ✓ "Create Your Account" heading
   ✓ Google OAuth button with Google logo
   ✓ Facebook OAuth button with Facebook logo
   ✓ Microsoft OAuth button with Microsoft logo
   ✓ Divider line with "OR"
   ✓ "Sign up with Email" button
   ✓ "Already have an account? Sign in" link
   ✓ Security badge at bottom
3. Check button styling and hover effects
4. Verify responsive design on mobile
```

### Test Case 2: Google OAuth Flow

**Objective**: Complete Google authentication and pre-fill registration form

```
1. On /register/social/, click "Continue with Google"
2. Verify redirected to Google login page
3. Log in with test Google account
4. Grant permission when prompted
5. Verify redirected back to http://localhost:8000/register/
6. Verify form shows:
   ✓ Email field pre-filled and read-only (locked icon)
   ✓ First name pre-filled (editable)
   ✓ Last name pre-filled (editable)
   ✓ Password field is disabled/read-only
   ✓ Google verification badge next to email
   ✓ "Verified by Google" info box at top
7. Profile picture should be visible (if logged in to Google)
8. Complete remaining required fields
9. Click "Create Comprehensive Account"
10. Verify user account created with:
    ✓ oauth_provider = 'google'
    ✓ oauth_id populated
    ✓ email_verified = True
    ✓ profile_image populated with Google picture
11. Verify redirected to login modal
12. Can log in with email (no password used from OAuth)
```

### Test Case 3: Facebook OAuth Flow

**Objective**: Complete Facebook authentication

```
1. On /register/social/, click "Continue with Facebook"
2. Verify redirected to Facebook login
3. Log in with test Facebook account
4. Grant permissions
5. Verify returned to /register/ with pre-filled data:
   ✓ Email field shows Facebook email
   ✓ First name and last name pre-filled
   ✓ Verification badge displayed
6. Complete form and submit
7. Verify Profile.oauth_provider = 'facebook'
8. Verify profile picture saved (if provided by Facebook)
```

### Test Case 4: Microsoft OAuth Flow

**Objective**: Complete Microsoft authentication

```
1. On /register/social/, click "Continue with Microsoft"
2. Verify redirected to Microsoft login
3. Log in with Microsoft account
4. Grant permissions
5. Verify returned to /register/ with pre-filled data:
   ✓ Email shows userPrincipalName or mail
   ✓ First/last name pre-filled
   ✓ Verification badge visible
6. Complete form and submit
7. Verify Profile.oauth_provider = 'microsoft'
```

### Test Case 5: Email Signup (Non-OAuth)

**Objective**: Verify fallback to email signup

```
1. Navigate to /register/social/
2. Click "Sign up with Email"
3. Verify redirected to /register/
4. Verify form shows:
   ✓ No verification badge
   ✓ Email field is editable
   ✓ Password fields are editable (not read-only)
   ✓ No OAuth info box
5. Fill in all form fields manually
6. Submit form
7. Verify account created with:
   ✓ oauth_provider = None
   ✓ email_verified = True
```

### Test Case 6: Existing Email Handling

**Objective**: Prevent duplicate accounts

```
1. Create account via Google with email@test.com
2. Try to register again with same email:
   - Via Google: Should show error "already exists"
   - Via Email signup: Should show error "already exists"
   - Via Facebook: Should show error "already exists"
3. Verify existing account not duplicated
```

### Test Case 7: Session Cleanup

**Objective**: Verify OAuth data cleared after registration

```
1. Complete OAuth registration flow
2. Verify in browser DevTools that session cleared after registration
3. Try accessing /register/ again without OAuth flow
4. Verify form shows no pre-filled data
5. Verify oauth_data not in session
```

### Test Case 8: Profile Picture Download

**Objective**: Verify profile pictures saved correctly

```
1. Register via Google with profile picture
2. Go to user profile page
3. Verify profile image displays correctly
4. Check media directory: media/profile_images/
5. Verify image file saved with format: {provider}_profile_{username}.{ext}
6. Repeat for Facebook (if picture available)
```

### Test Case 9: Password Reset for OAuth Users

**Objective**: Verify OAuth users can set password if needed

```
1. Register via OAuth (no password set)
2. Navigate to password reset page
3. Enter OAuth-registered email
4. Verify can set new password
5. Log in with new password
6. Verify works correctly
```

### Test Case 10: Mobile Responsiveness

**Objective**: Verify responsive design on mobile

```
1. Open /register/social/ on mobile device (or DevTools)
2. Verify:
   ✓ Buttons stack vertically
   ✓ All text readable (no cutoff)
   ✓ Touch targets are adequate size (>44px)
   ✓ No horizontal scroll
3. Complete OAuth flow on mobile
4. Verify form displays correctly on mobile
5. Test form submission on mobile
```

### Test Case 11: Error Handling

**Objective**: Verify graceful error handling

```
1. Test invalid OAuth state:
   - Manually modify state parameter in URL
   - Verify error message displayed
   
2. Test OAuth provider error:
   - Decline permissions on provider login
   - Verify error message: "Authentication failed"
   
3. Test network error:
   - Simulate network failure during token exchange
   - Verify user-friendly error message
   
4. Test OAuth response without code:
   - Manually access callback without code param
   - Verify error handling
```

### Test Case 12: CSRF Protection

**Objective**: Verify OAuth flow protected from CSRF

```
1. Register via OAuth normally
2. Inspect network requests
3. Verify:
   ✓ State parameter verified on callback
   ✓ CSRF token validated in forms
   ✓ Session-based CSRF tokens working
```

### Test Case 13: Admin Dashboard

**Objective**: Verify OAuth data visible in admin

```
1. Log in to Django admin
2. Navigate to Users → Profiles
3. Select an OAuth-registered user
4. Verify profile shows:
   ✓ oauth_provider field populated
   ✓ oauth_id populated
   ✓ email_verified = True
   ✓ profile_image saved
```

### Test Case 14: Duplicate OAuth ID Detection

**Objective**: Verify same OAuth account can't create multiple registrations

```
1. Register with Google account
2. Log out
3. Try to register again with same Google account
4. Should show: "Email already registered"
5. Verify only one Profile record exists
```

### Test Case 15: Production Redirect URI

**Objective**: Test with production domain

```
1. Update .env with production URLs
2. Test OAuth flow with https://yourdomain.com
3. Verify redirect URIs match provider settings
4. Complete full OAuth flow on production domain
```

---

## Debugging

### Common Issues

#### 1. "OAuth X is not configured"

**Symptom**: Error message when clicking OAuth button

**Solution**:
- Check .env file has correct environment variables
- Verify `SOCIALACCOUNT_PROVIDERS` settings in settings.py
- Restart Django server after changing .env

#### 2. "State mismatch"

**Symptom**: OAuth callback shows "Authentication state mismatch"

**Solution**:
- Clear browser cookies/session
- Try again from fresh browser session
- Check session backend configured correctly

#### 3. "Profile picture not saving"

**Symptom**: OAuth user created but profile image empty

**Solution**:
- Check media directory exists and is writable
- Verify picture URL is valid (test in browser)
- Check network connectivity for image download
- Look at Django logs for download errors

#### 4. "Email already exists for OAuth"

**Symptom**: Can't register with OAuth due to existing email

**Solution**:
- Merge accounts if user has both OAuth and email account
- Consider OAuth account linking feature

#### 5. "Invalid client_id"

**Symptom**: OAuth provider rejects request

**Solution**:
- Verify client ID matches OAuth provider settings
- Check for typos in .env
- Ensure redirect URIs match exactly (including protocol/port)

---

## Production Deployment Checklist

- [ ] All environment variables set on production server
- [ ] OAuth redirect URIs configured in all provider dashboards
- [ ] HTTPS enforced (required for OAuth)
- [ ] Database migrations applied
- [ ] Media directory exists and is writable
- [ ] Django server restarted
- [ ] Test OAuth flow end-to-end on production
- [ ] Monitor error logs for OAuth issues
- [ ] Set up alerts for authentication failures
- [ ] Backup OAuth credentials in secure vault

---

## Performance Optimization

### Profile Picture Download Optimization

The profile picture download is non-blocking. If download fails:
- Original URL stored in `oauth_picture_url` field
- User can still complete registration
- Picture can be retried later

### Session Data Storage

- OAuth data stored temporarily in session only
- Cleared immediately after account creation
- No persistent storage of OAuth tokens
- Session timeout ensures cleanup

---

## Security Considerations

### OAuth Best Practices Implemented

1. **State Parameter Verification**
   - Random state generated for each OAuth flow
   - State verified on callback to prevent CSRF
   - Invalid states rejected with error

2. **HTTPS Required**
   - OAuth only works over secure HTTPS
   - Redirect URIs must match exactly
   - All tokens transmitted securely

3. **No Token Storage**
   - Access tokens not persisted
   - Used only for immediate data retrieval
   - Tokens discarded after use

4. **Email Verification**
   - OAuth provider's email verification trusted
   - email_verified flag set automatically
   - No duplicate email verification needed

5. **Password Security**
   - OAuth users get random password
   - Can reset via standard password reset flow
   - Passwords never stored for OAuth-only users

6. **Profile Picture Security**
   - Only downloaded from official provider domains
   - Virus scan recommended before serving
   - User can replace picture if needed

---

## Integration with Existing Features

### Compatible With

- ✓ User profiles
- ✓ Program registration
- ✓ Candidates management
- ✓ Email notifications
- ✓ Application tracking
- ✓ Document uploads
- ✓ Password reset flow

### Session Management

- OAuth data stored in request.session
- Automatic cleanup after 2 weeks (Django default)
- Manual cleanup after successful registration
- No database storage of OAuth credentials

---

## Future Enhancements

### Potential Features

1. **Account Linking**
   - Link multiple OAuth providers to one account
   - Switch between providers for login

2. **Social Sharing**
   - Share programs via social media
   - Pre-populated profile data

3. **Additional Providers**
   - Apple ID
   - GitHub
   - LinkedIn

4. **Enhanced Profile Data**
   - Retrieve more detailed data from providers
   - Auto-fill additional profile fields
   - Social media integration

5. **Two-Factor Authentication**
   - OAuth with 2FA for added security
   - Integration with authenticator apps

---

## Support & Resources

### Documentation

- [Django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth Setup](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Guide](https://developers.facebook.com/docs/facebook-login)
- [Microsoft OAuth Setup](https://docs.microsoft.com/en-us/azure/active-directory/develop/)

### Contact

For issues or questions about OAuth integration, refer to the main project documentation or contact the development team.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-26 | Initial OAuth 2.0 implementation with Google, Facebook, Microsoft providers |

---

*Last Updated: November 26, 2025*
