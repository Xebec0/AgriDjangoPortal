"""
Management command to setup OAuth providers in django-allauth
Usage: python manage.py setup_oauth
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Setup OAuth providers (Google, Facebook, Microsoft) in django-allauth'

    def handle(self, *args, **options):
        # Get or create the default site
        site, site_created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'AgroStudies'
            }
        )
        
        if site_created:
            self.stdout.write(self.style.SUCCESS('✅ Created default site'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Using existing site'))

        # Setup Google OAuth
        google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '105868296186-0mrgu1eh9ior46oqgmgvgctdfde31v64.apps.googleusercontent.com')
        google_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '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')
        
        google_app, google_created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
            }
        )
        
        if not google_app.sites.filter(pk=site.pk).exists():
            google_app.sites.add(site)
        
        if google_created:
            self.stdout.write(self.style.SUCCESS('✅ Created Google OAuth app'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Google OAuth app already exists'))
        
        self.stdout.write(f'   Provider: {google_app.provider}')
        self.stdout.write(f'   Client ID: {google_app.client_id[:30]}...')
        self.stdout.write(f'   Sites: {list(google_app.sites.all())}')

        # Setup Facebook OAuth
        facebook_client_id = os.getenv('FACEBOOK_OAUTH_CLIENT_ID', '')
        facebook_secret = os.getenv('FACEBOOK_OAUTH_CLIENT_SECRET', '')
        
        if facebook_client_id and facebook_secret:
            facebook_app, facebook_created = SocialApp.objects.get_or_create(
                provider='facebook',
                defaults={
                    'name': 'Facebook',
                    'client_id': facebook_client_id,
                    'secret': facebook_secret,
                }
            )
            
            if not facebook_app.sites.filter(pk=site.pk).exists():
                facebook_app.sites.add(site)
            
            if facebook_created:
                self.stdout.write(self.style.SUCCESS('✅ Created Facebook OAuth app'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Facebook OAuth app already exists'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Facebook OAuth credentials not configured'))

        # Setup Microsoft OAuth
        microsoft_client_id = os.getenv('MICROSOFT_OAUTH_CLIENT_ID', '')
        microsoft_secret = os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET', '')
        
        if microsoft_client_id and microsoft_secret:
            microsoft_app, microsoft_created = SocialApp.objects.get_or_create(
                provider='microsoft',
                defaults={
                    'name': 'Microsoft',
                    'client_id': microsoft_client_id,
                    'secret': microsoft_secret,
                }
            )
            
            if not microsoft_app.sites.filter(pk=site.pk).exists():
                microsoft_app.sites.add(site)
            
            if microsoft_created:
                self.stdout.write(self.style.SUCCESS('✅ Created Microsoft OAuth app'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Microsoft OAuth app already exists'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  Microsoft OAuth credentials not configured'))

        self.stdout.write('\n' + self.style.SUCCESS('✅ OAuth setup complete!'))
        self.stdout.write(self.style.WARNING('\nℹ️  Note: Provider apps must match the Site domain for callbacks to work.'))
