from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
        import core.cache_signals  # Import cache invalidation signals

        # Auto-provision OAuth apps after migrations complete
        from django.db.models.signals import post_migrate
        post_migrate.connect(_provision_oauth_apps, sender=self)


def _provision_oauth_apps(sender, **kwargs):
    """
    Auto-provision OAuth SocialApp records from environment variables
    after migrations complete. Ensures OAuth works on Render deploys
    without relying solely on the setup_oauth management command.
    """
    import os
    import logging

    logger = logging.getLogger(__name__)

    # Only proceed if at least Google credentials are set
    if not os.getenv('GOOGLE_OAUTH_CLIENT_ID'):
        return

    try:
        from django.contrib.sites.models import Site
        from core.oauth_utils import ensure_social_app

        site_domain = os.getenv('SITE_DOMAIN', 'localhost:8000')
        site_name = os.getenv('SITE_NAME', 'AgroStudies')

        # Ensure correct site domain
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={'domain': site_domain, 'name': site_name}
        )
        if not created and site.domain != site_domain:
            site.domain = site_domain
            site.name = site_name
            site.save()

        # Provision each configured provider
        for provider in ('google', 'facebook', 'microsoft'):
            app = ensure_social_app(provider)
            if app and not app.sites.filter(pk=site.pk).exists():
                app.sites.add(site)

        logger.info(f"[OAuth] Auto-provision complete (site: {site_domain})")
    except Exception as e:
        logger.warning(f"[OAuth] Auto-provision skipped: {e}")
