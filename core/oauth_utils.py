"""
OAuth 2.0 Utilities for Social Authentication Integration
Handles OAuth flow, data retrieval, and profile picture management
"""

import requests
import logging
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import json
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class OAuthDataExtractor:
    """Extracts user data from different OAuth providers"""
    
    @staticmethod
    def get_google_user_data(access_token):
        """
        Fetch Google user profile data using access token
        Returns: dict with email, first_name, last_name, picture
        """
        try:
            url = "https://www.googleapis.com/oauth2/v1/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            user_data = response.json()
            
            return {
                'provider': 'google',
                'oauth_id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'picture': user_data.get('picture'),
                'email_verified': user_data.get('verified_email', False),
            }
        except Exception as e:
            logger.error(f"Error fetching Google user data: {e}")
            return None
    
    @staticmethod
    def get_facebook_user_data(access_token):
        """
        Fetch Facebook user profile data using access token
        Returns: dict with email, first_name, last_name, picture
        """
        try:
            url = "https://graph.facebook.com/v15.0/me"
            params = {
                'access_token': access_token,
                'fields': 'id,email,first_name,last_name,picture.width(200).height(200)'
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            user_data = response.json()
            
            picture_url = None
            if 'picture' in user_data and 'data' in user_data['picture']:
                picture_url = user_data['picture']['data'].get('url')
            
            return {
                'provider': 'facebook',
                'oauth_id': user_data.get('id'),
                'email': user_data.get('email'),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'picture': picture_url,
                'email_verified': True if user_data.get('email') else False,
            }
        except Exception as e:
            logger.error(f"Error fetching Facebook user data: {e}")
            return None
    
    @staticmethod
    def get_microsoft_user_data(access_token):
        """
        Fetch Microsoft user profile data using access token
        Returns: dict with email, first_name, last_name, picture
        """
        try:
            # Get basic profile info
            url = "https://graph.microsoft.com/v1.0/me"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            user_data = response.json()
            
            # Try to get profile picture
            picture_url = None
            try:
                photo_url = "https://graph.microsoft.com/v1.0/me/photo/$value"
                photo_response = requests.get(photo_url, headers=headers, timeout=10)
                if photo_response.status_code == 200:
                    # Store as base64 or upload directly
                    picture_url = f"data:image/jpeg;base64,{photo_response.content}"
            except Exception as e:
                logger.warning(f"Could not fetch Microsoft profile picture: {e}")
            
            return {
                'provider': 'microsoft',
                'oauth_id': user_data.get('id'),
                'email': user_data.get('userPrincipalName') or user_data.get('mail'),
                'first_name': user_data.get('givenName', ''),
                'last_name': user_data.get('surname', ''),
                'picture': picture_url,
                'email_verified': True if user_data.get('mail') else False,
            }
        except Exception as e:
            logger.error(f"Error fetching Microsoft user data: {e}")
            return None


class OAuthTokenExchanger:
    """Exchanges authorization codes for access tokens"""
    
    @staticmethod
    def exchange_google_code(code, redirect_uri):
        """Exchange Google authorization code for access token"""
        try:
            from allauth.socialaccount.models import SocialApp
            
            # Get credentials from database instead of settings
            google_app = SocialApp.objects.get(provider='google')
            client_id = google_app.client_id
            client_secret = google_app.secret
            
            url = "https://oauth2.googleapis.com/token"
            data = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token'), token_data.get('id_token')
        except Exception as e:
            logger.error(f"Error exchanging Google code: {e}")
            return None, None
    
    @staticmethod
    def exchange_facebook_code(code, redirect_uri):
        """Exchange Facebook authorization code for access token"""
        try:
            from allauth.socialaccount.models import SocialApp
            
            # Get credentials from database instead of settings
            facebook_app = SocialApp.objects.get(provider='facebook')
            client_id = facebook_app.client_id
            client_secret = facebook_app.secret
            
            url = "https://graph.facebook.com/v15.0/oauth/access_token"
            
            params = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token'), None
        except Exception as e:
            logger.error(f"Error exchanging Facebook code: {e}")
            return None, None
    
    @staticmethod
    def exchange_microsoft_code(code, redirect_uri):
        """Exchange Microsoft authorization code for access token"""
        try:
            from allauth.socialaccount.models import SocialApp
            
            # Get credentials from database instead of settings
            microsoft_app = SocialApp.objects.get(provider='microsoft')
            client_id = microsoft_app.client_id
            client_secret = microsoft_app.secret
            
            url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'scope': 'https://graph.microsoft.com/.default',
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data.get('access_token'), None
        except Exception as e:
            logger.error(f"Error exchanging Microsoft code: {e}")
            return None, None


class ProfilePictureDownloader:
    """Downloads and saves profile pictures from OAuth providers"""
    
    @staticmethod
    def download_and_save_picture(profile, picture_url, provider):
        """
        Download profile picture from URL and save to profile_image field
        Returns: True if successful, False otherwise
        """
        if not picture_url or picture_url.startswith('data:'):
            # Skip base64 or invalid URLs
            return False
        
        try:
            response = requests.get(picture_url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension based on content type
            content_type = response.headers.get('content-type', 'image/jpeg')
            if 'png' in content_type:
                ext = 'png'
            elif 'gif' in content_type:
                ext = 'gif'
            else:
                ext = 'jpg'
            
            filename = f"{provider}_profile_{profile.user.username}.{ext}"
            image_content = ContentFile(response.content, name=filename)
            
            # Save to profile
            profile.profile_image = image_content
            profile.oauth_picture_url = picture_url
            profile.save(update_fields=['profile_image', 'oauth_picture_url'])
            
            logger.info(f"Successfully downloaded profile picture for {profile.user.username} from {provider}")
            return True
        except Exception as e:
            logger.error(f"Error downloading profile picture from {picture_url}: {e}")
            # Save URL for reference even if download fails
            try:
                profile.oauth_picture_url = picture_url
                profile.save(update_fields=['oauth_picture_url'])
            except Exception as save_error:
                logger.error(f"Error saving OAuth picture URL: {save_error}")
            return False


def store_oauth_session_data(request, oauth_data):
    """
    Store OAuth data in session for use during registration form
    """
    request.session['oauth_data'] = {
        'provider': oauth_data.get('provider'),
        'oauth_id': oauth_data.get('oauth_id'),
        'email': oauth_data.get('email'),
        'first_name': oauth_data.get('first_name'),
        'last_name': oauth_data.get('last_name'),
        'picture': oauth_data.get('picture'),
        'email_verified': oauth_data.get('email_verified', False),
    }
    request.session.modified = True


def get_oauth_session_data(request):
    """
    Retrieve OAuth data from session
    """
    return request.session.get('oauth_data', {})


def clear_oauth_session_data(request):
    """
    Clear OAuth data from session after successful registration
    """
    if 'oauth_data' in request.session:
        del request.session['oauth_data']
        request.session.modified = True


def ensure_social_app(provider):
    """
    Get or create a SocialApp for the given provider using environment variables.
    Returns the SocialApp instance or None if credentials aren't configured.
    This acts as a self-healing fallback when DB records are missing.
    """
    import os

    ENV_KEYS = {
        'google': ('GOOGLE_OAUTH_CLIENT_ID', 'GOOGLE_OAUTH_CLIENT_SECRET'),
        'facebook': ('FACEBOOK_OAUTH_CLIENT_ID', 'FACEBOOK_OAUTH_CLIENT_SECRET'),
        'microsoft': ('MICROSOFT_OAUTH_CLIENT_ID', 'MICROSOFT_OAUTH_CLIENT_SECRET'),
    }

    # First, try to get from database
    try:
        from allauth.socialaccount.models import SocialApp
        return SocialApp.objects.get(provider=provider)
    except SocialApp.DoesNotExist:
        pass
    except Exception as e:
        logger.warning(f"[OAuth] DB lookup failed for {provider}: {e}")
        return None

    # Not in DB — try to auto-create from environment variables
    keys = ENV_KEYS.get(provider)
    if not keys:
        logger.warning(f"[OAuth] Unknown provider: {provider}")
        return None

    client_id = os.getenv(keys[0], '')
    client_secret = os.getenv(keys[1], '')

    if not client_id or not client_secret:
        logger.error(f"[OAuth] {provider} env vars ({keys[0]}, {keys[1]}) not set")
        return None

    try:
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site

        app = SocialApp.objects.create(
            provider=provider,
            name=provider.title(),
            client_id=client_id,
            secret=client_secret,
        )

        # Associate with default site
        try:
            site = Site.objects.get(id=1)
            app.sites.add(site)
        except Site.DoesNotExist:
            pass

        logger.info(f"[OAuth] Auto-created {provider} SocialApp from environment")
        return app
    except Exception as e:
        logger.error(f"[OAuth] Failed to auto-create {provider} SocialApp: {e}")
        return None
