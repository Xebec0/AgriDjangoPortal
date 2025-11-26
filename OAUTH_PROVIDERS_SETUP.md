# OAuth Providers Setup Guide

This guide will walk you through setting up Google, Facebook, and Microsoft OAuth 2.0 authentication for the AgroStudies platform.

## Table of Contents
1. [Google OAuth Setup](#google-oauth-setup)
2. [Facebook OAuth Setup](#facebook-oauth-setup)
3. [Microsoft OAuth Setup](#microsoft-oauth-setup)
4. [Environment Configuration](#environment-configuration)
5. [Testing the Integration](#testing-the-integration)
6. [Troubleshooting](#troubleshooting)

---

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account (or create a new one)
3. Click on the project dropdown at the top
4. Click "NEW PROJECT"
5. Enter project name: `AgroStudies` (or your preferred name)
6. Click "CREATE"

### Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it
4. Click the "ENABLE" button
5. Wait for it to enable (usually takes a few seconds)

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "CREATE CREDENTIALS" > "OAuth client ID"
3. If prompted to create a consent screen first:
   - Click "CONFIGURE CONSENT SCREEN"
   - Select "External" as User Type
   - Click "CREATE"
   - Fill in required fields:
     - **App name:** AgroStudies
     - **User support email:** your-email@gmail.com
     - **Developer contact email:** your-email@gmail.com
   - Click "SAVE AND CONTINUE"
   - Skip optional scopes, click "SAVE AND CONTINUE"
   - Click "BACK TO DASHBOARD"
4. Return to "Credentials" and click "CREATE CREDENTIALS" > "OAuth client ID"
5. Select **"Web application"** as the application type
6. Under "Authorized JavaScript origins," click "ADD URI" and add:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - `https://yourdomain.com` (for production)
7. Under "Authorized redirect URIs," click "ADD URI" and add:
   - `http://localhost:8000/auth/google/callback/`
   - `http://127.0.0.1:8000/auth/google/callback/`
   - `https://yourdomain.com/auth/google/callback/` (for production)
8. Click "CREATE"
9. A popup will show your credentials. Copy:
   - **Client ID**
   - **Client Secret**

### Step 4: Save Google Credentials

Save these credentials in your `.env` file:
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id_here
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
```

---

## Facebook OAuth Setup

### Step 1: Create a Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Sign in with your Facebook account (or create a new one)
3. Click "My Apps" in the top navigation
4. Click "Create App"
5. Select "Consumer" as the app type
6. Click "Next"
7. Fill in the required information:
   - **App Name:** AgroStudies
   - **App Contact Email:** your-email@example.com
   - **App Purpose:** Choose "Agriculture" or the closest category
8. Click "Create App"
9. Complete the security check if prompted

### Step 2: Add Facebook Login Product

1. In your app dashboard, click "Add Product"
2. Find "Facebook Login" and click "Set Up"
3. Select "Web" as your platform
4. Follow the setup wizard (you can skip most steps)

### Step 3: Configure Facebook Login Settings

1. Go to "Products" > "Facebook Login" > "Settings"
2. Under "Valid OAuth Redirect URIs," add:
   - `http://localhost:8000/auth/facebook/callback/`
   - `http://127.0.0.1:8000/auth/facebook/callback/`
   - `https://yourdomain.com/auth/facebook/callback/` (for production)
3. Click "Save Changes"

### Step 4: Get Your App Credentials

1. Go to "Settings" > "Basic"
2. You'll see:
   - **App ID**
   - **App Secret** (click "Show" to reveal)
3. Copy both values

### Step 5: Configure App Domains

1. Go to "Settings" > "Basic"
2. Scroll down to "App Domains"
3. Add:
   - `localhost:8000`
   - `127.0.0.1:8000`
   - `yourdomain.com` (for production)
4. Click "Save Changes"

### Step 6: Save Facebook Credentials

Save these credentials in your `.env` file:
```
FACEBOOK_OAUTH_CLIENT_ID=your_app_id_here
FACEBOOK_OAUTH_CLIENT_SECRET=your_app_secret_here
```

---

## Microsoft OAuth Setup

### Step 1: Register Your Application

1. Go to [Microsoft Azure Portal](https://portal.azure.com/)
2. Sign in with your Microsoft account (or create a new one)
3. Search for "App registrations" in the top search bar
4. Click "App registrations"
5. Click "New registration"
6. Fill in the registration form:
   - **Name:** AgroStudies
   - **Supported account types:** Select "Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)"
   - **Redirect URI:** Select "Web" and enter `http://localhost:8000/auth/microsoft/callback/`
7. Click "Register"

### Step 2: Configure Redirect URIs

1. In your app registration, go to "Authentication" in the left sidebar
2. Under "Web," you should see the redirect URI you added
3. Click "Add a Redirect URI"
4. Add additional URIs:
   - `http://127.0.0.1:8000/auth/microsoft/callback/`
   - `https://yourdomain.com/auth/microsoft/callback/` (for production)
5. Click "Save"

### Step 3: Create Client Secret

1. Go to "Certificates & secrets" in the left sidebar
2. Click "New client secret"
3. Enter a description: `AgroStudies OAuth Secret`
4. Select expiration: "12 months" (or your preferred duration)
5. Click "Add"
6. **IMPORTANT:** Copy the "Value" (not the ID) immediately - you won't be able to see it again!

### Step 4: Get Your Application ID

1. Go back to "Overview"
2. Copy the **Application (client) ID**
3. Also note the **Directory (tenant) ID** (you may need this for production)

### Step 5: Save Microsoft Credentials

Save these credentials in your `.env` file:
```
MICROSOFT_OAUTH_CLIENT_ID=your_application_id_here
MICROSOFT_OAUTH_CLIENT_SECRET=your_client_secret_here
```

---

## Environment Configuration

### Step 1: Create/Update `.env` File

Create a `.env` file in the project root directory:

```bash
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

# Facebook OAuth
FACEBOOK_OAUTH_CLIENT_ID=your_facebook_app_id
FACEBOOK_OAUTH_CLIENT_SECRET=your_facebook_app_secret

# Microsoft OAuth
MICROSOFT_OAUTH_CLIENT_ID=your_microsoft_app_id
MICROSOFT_OAUTH_CLIENT_SECRET=your_microsoft_client_secret

# Django Settings
DEBUG=True
SECRET_KEY=your_django_secret_key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Step 2: Update Django Settings

The `settings.py` is already configured with these environment variables. Verify the following section exists:

```python
# OAuth Configuration (in settings.py)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'FIELDS': [
            'id',
            'email',
            'name',
            'picture',
            'locale',
        ]
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/en_US/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'rerequest'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'email',
            'name',
            'picture',
            'locale',
        ]
    },
    'microsoft': {
        'SCOPE': [
            'User.Read',
            'email',
        ],
        'AUTH_PARAMS': {
            'prompt': 'select_account',
        },
        'FIELDS': [
            'id',
            'mail',
            'givenName',
            'surname',
            'picture',
        ]
    }
}
```

---

## Testing the Integration

### Step 1: Start Django Development Server

```bash
python manage.py runserver
```

### Step 2: Navigate to Social Registration

1. Open your browser
2. Go to `http://localhost:8000/register/social/`
3. You should see three OAuth provider buttons:
   - **Continue with Google**
   - **Continue with Facebook**
   - **Continue with Microsoft**

### Step 3: Test Google OAuth

1. Click "Continue with Google"
2. You'll be redirected to Google's login page
3. Sign in with your Google account
4. Grant permissions when prompted
5. You should be redirected back to the form with pre-filled data:
   - Email
   - First Name
   - Last Name (if available)
   - Profile Picture

### Step 4: Test Facebook OAuth

1. Go back to `http://localhost:8000/register/social/`
2. Click "Continue with Facebook"
3. Follow the same process as Google
4. Verify pre-filled data

### Step 5: Test Microsoft OAuth

1. Go back to `http://localhost:8000/register/social/`
2. Click "Continue with Microsoft"
3. Follow the same process
4. Verify pre-filled data

### Step 6: Verify Account Creation

1. After completing the OAuth flow, the form should be pre-filled
2. Click "NEXT" or "CREATE ACCOUNT"
3. Verify that:
   - Account is created with the OAuth provider data
   - Email is verified automatically
   - Profile picture is downloaded
   - `oauth_provider` field is set correctly

---

## Troubleshooting

### Issue: "OAuth Provider Not Configured"

**Solution:** 
- Ensure all credentials are in your `.env` file
- Restart the Django server: `python manage.py runserver`
- Check that environment variables are loaded correctly

### Issue: "Redirect URI Mismatch"

**Solution:**
- Verify the redirect URI in each provider's settings matches exactly:
  - For local dev: `http://localhost:8000/auth/{provider}/callback/`
  - For production: `https://yourdomain.com/auth/{provider}/callback/`
- No trailing slashes or protocol mismatches
- Restart Django server after making changes

### Issue: "Invalid Client ID"

**Solution:**
- Double-check the Client ID (not Secret) is correct
- Make sure you're using the right value for each provider
- Copy-paste to avoid typos

### Issue: User Data Not Pre-Filling

**Solution:**
- Check browser console for JavaScript errors
- Verify the OAuth callback is working (check server logs)
- Ensure user has granted permission to share email and profile data
- Check that the user data extraction functions are working:
  ```python
  # In terminal, with Django shell
  python manage.py shell
  from core.oauth_utils import OAuthDataExtractor
  # Test extraction with sample token
  ```

### Issue: Profile Picture Not Downloading

**Solution:**
- Check Django logs for errors during picture download
- Verify the media folder has write permissions:
  ```bash
  chmod 755 media/
  ```
- Ensure the picture URL from provider is accessible
- Check that Pillow is installed:
  ```bash
  pip install Pillow
  ```

### Issue: Email Not Verified Automatically

**Solution:**
- Verify the email is included in the OAuth provider's scope
- Check that the `email_verified` flag is being set in `views.py`
- Ensure the registration flow saves this flag to the user profile

### Issue: Session Data Lost

**Solution:**
- Verify Django sessions are enabled in settings.py
- Clear browser cookies/cache
- Ensure `SESSION_ENGINE` is set correctly:
  ```python
  SESSION_ENGINE = 'django.contrib.sessions.backends.db'
  ```
- Run migrations if session tables are missing:
  ```bash
  python manage.py migrate
  ```

---

## Production Deployment Checklist

Before deploying to production:

- [ ] Update all redirect URIs to use your production domain
- [ ] Ensure OAuth credentials are stored in environment variables (not hardcoded)
- [ ] Test all three OAuth providers in staging environment
- [ ] Set `DEBUG = False` in Django settings
- [ ] Enable HTTPS (OAuth requires HTTPS in production)
- [ ] Update `ALLOWED_HOSTS` in settings
- [ ] Configure CSRF settings appropriately
- [ ] Test email verification with real email addresses
- [ ] Set up proper error logging and monitoring
- [ ] Review security settings with your DevOps team

---

## Additional Resources

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Documentation](https://developers.facebook.com/docs/facebook-login)
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [django-allauth Documentation](https://django-allauth.readthedocs.io/)

---

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review Django server logs for error messages
3. Check browser console for JavaScript errors
4. Verify all credentials are correct
5. Ensure all redirect URIs match exactly
6. Contact support with the specific error message

