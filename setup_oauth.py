#!/usr/bin/env python
"""
Script to register OAuth providers in django-allauth
Run with: python manage.py shell < setup_oauth.py
"""
import os
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# Get or create the site
site, _ = Site.objects.get_or_create(
    id=1,
    defaults={
        'domain': 'localhost:8000',
        'name': 'AgroStudies'
    }
)

# Google OAuth
google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID', '105868296186-0mrqu1eh9lor46oqgmvqctdfde31v64.apps.googleusercontent.com'),
        'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', 'GOCSPX-f0G_MFKLDWABXkgTbGBXl6eC-sQ'),
    }
)
if created:
    google_app.sites.add(site)
    print('✅ Google OAuth app created successfully')
else:
    print('✅ Google OAuth app already exists')

print(f'Provider: {google_app.provider}')
print(f'Client ID: {google_app.client_id[:30]}...')
print(f'Sites: {list(google_app.sites.all())}')
