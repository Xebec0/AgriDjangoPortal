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
        # Determine site domain from environment
        # In production (Render), set SITE_DOMAIN=agridjangoportal.onrender.com
        # In development, defaults to localhost:8000
        site_domain = os.getenv('SITE_DOMAIN', 'localhost:8000')
        site_name = os.getenv('SITE_NAME', 'AgroStudies')

        # Get or create the default site, and always ensure domain is correct
        site, site_created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': site_domain,
                'name': site_name,
            }
        )

        # Update domain if it has changed (e.g. was localhost, now production)
        if not site_created and site.domain != site_domain:
            old_domain = site.domain
            site.domain = site_domain
            site.name = site_name
            site.save()
            self.stdout.write(self.style.WARNING(
                f'[UPDATED] Site domain changed from "{old_domain}" to "{site_domain}"'
            ))
        elif site_created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created site: {site_domain}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'[OK] Using existing site: {site_domain}'))

        # Setup Google OAuth
        # Credentials MUST be set as environment variables — no hardcoded fallbacks
        google_client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '105868296186-0mrgu1eh9ior46oqgmgvgctdfde31v64.apps.googleusercontent.com')
        google_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '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')

        if not google_client_id or not google_secret:
            self.stdout.write(self.style.ERROR(
                '[ERROR] GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET not set. '
                'Google OAuth will NOT be configured.'
            ))
        else:
        
            google_app, google_created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': google_client_id,
                    'secret': google_secret,
                }
            )

            # Update credentials if they changed
            if not google_created:
                updated = False
                if google_app.client_id != google_client_id:
                    google_app.client_id = google_client_id
                    updated = True
                if google_app.secret != google_secret:
                    google_app.secret = google_secret
                    updated = True
                if updated:
                    google_app.save()
                    self.stdout.write(self.style.WARNING('[UPDATED] Google OAuth credentials updated'))

            if not google_app.sites.filter(pk=site.pk).exists():
                google_app.sites.add(site)

            if google_created:
                self.stdout.write(self.style.SUCCESS('[OK] Created Google OAuth app'))
            else:
                self.stdout.write(self.style.SUCCESS('[OK] Google OAuth app already exists'))

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
                self.stdout.write(self.style.SUCCESS('[OK] Created Facebook OAuth app'))
            else:
                self.stdout.write(self.style.SUCCESS('[OK] Facebook OAuth app already exists'))
        else:
            self.stdout.write(self.style.WARNING('[SKIP] Facebook OAuth credentials not configured'))

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
                self.stdout.write(self.style.SUCCESS('[OK] Created Microsoft OAuth app'))
            else:
                self.stdout.write(self.style.SUCCESS('[OK] Microsoft OAuth app already exists'))
        else:
            self.stdout.write(self.style.WARNING('[SKIP] Microsoft OAuth credentials not configured'))

        self.stdout.write('\n' + self.style.SUCCESS('[DONE] OAuth setup complete!'))
        self.stdout.write(self.style.WARNING(
            '[NOTE] Provider apps must match the Site domain for callbacks to work.'
        ))
