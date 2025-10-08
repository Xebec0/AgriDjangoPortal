# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project: Agrostudies Registration System for Farm Selection (Django)

Core assumptions
- Python: Prefer 3.11 (pyproject specifies >=3.11; Render config pins 3.11). README mentions 3.8+, but align local dev with 3.11 for consistency.
- Default settings module: agrostudies_project.settings (manage.py sets this automatically).

Common commands
- Setup (first run)
  ```bash path=null start=null
  # Create & activate venv (PowerShell)
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1

  # Install dependencies
  pip install -r requirements.txt

  # Initialize env (copy template and edit as needed)
  copy .env.example .env

  # Bootstrap DB
  python manage.py migrate
  python manage.py createsuperuser  # or: python manage.py createsu

  # Collect static (useful locally when DEBUG=False or to mirror prod)
  python manage.py collectstatic --noinput
  ```

- Run the dev server
  ```bash path=null start=null
  python manage.py runserver
  ```

- Tests
  ```bash path=null start=null
  # Run all tests (Django test runner)
  python manage.py test

  # Run a single test module
  python manage.py test core.tests.test_views

  # With coverage
  pip install coverage
  coverage run --source='.' manage.py test
  coverage report

  # Optional (pytest is in requirements):
  # Run all tests
  pytest -q
  # Run a single file
  pytest core/tests/test_views.py -q
  # Filter by test name pattern
  pytest -k "test_name_fragment" -q
  ```

- Management commands (commonly used)
  ```bash path=null start=null
  # Create superuser via custom command (non-interactive possible via env)
  python manage.py createsu

  # Manual DB backup
  python manage.py backup_db

  # Scheduled backup (used by cron/Render cron)
  python manage.py scheduled_backup
  ```

- Production-like run (local) and deploy hooks
  ```bash path=null start=null
  # Production WSGI entry
  gunicorn agrostudies_project.wsgi:application

  # Render build & start (as per render.yaml)
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  gunicorn agrostudies_project.wsgi:application

  # Post-deploy tasks on Render
  python manage.py migrate --noinput && python manage.py createsu
  ```

- Security/Vulnerability scan (optional but available)
  ```bash path=null start=null
  pip-audit -r requirements.txt
  ```

High-level architecture and structure
- Django project layout
  - agrostudies_project/ holds framework scaffolding:
    - settings.py: Central configuration. Highlights:
      - INSTALLED_APPS includes core (primary app) and django_crontab. Optionally adds cachalot (if installed) and debug_toolbar when DEBUG=True.
      - Middleware includes WhiteNoise for static, custom core.middleware.RequestContextMiddleware, and (in DEBUG) debug toolbar.
      - Database via dj-database-url: defaults to sqlite:///db.sqlite3 when DATABASE_URL is unset.
      - Static files: STATICFILES_DIRS=[static], STATIC_ROOT=staticfiles. During tests, uses StaticFilesStorage to avoid manifest issues; otherwise WhiteNoise CompressedManifest.
      - Email: Configurable via env; defaults to SMTP (Gmail sample in .env.example). In DEBUG with no credentials, can switch to console backend.
      - Logging: RotatingFileHandler to logs/app.log plus console, level from LOG_LEVEL (env).
      - Caching: Uses Redis (django-redis) when REDIS_URL is set, with JSON serialization and compression; falls back to local memory cache. Optional ORM caching via cachalot.
      - Security: Production toggles SSL redirects, secure cookies, security headers, and HSTS. CSRF_TRUSTED_ORIGINS includes localhost and Render domains. Rate limiting feature flag (RATELIMIT_ENABLE) disables during tests.
      - Cron: django-crontab schedules daily scheduled_backup at 17:00 UTC.
    - urls.py: Routes admin/ and includes core.urls at root. In DEBUG, mounts debug toolbar and serves static/media.
    - asgi.py / wsgi.py: Standard application entry points.
  - core/ is the main business app. Responsibilities inferred from urls and README:
    - Authentication & profiles: register/login/logout, profile management, admin self-registration (admin_register) gated by ADMIN_REGISTRATION_CODE.
    - Program & application workflow: list programs, details, apply, registrants, registration detail and status updates, cancellations.
    - Documents: upload/validate (Pillow in requirements suggests image handling).
    - Notifications: list, mark read, clear, basic API endpoints for async UX.
    - Exports: CSV/Excel/PDF for candidates and program registrants (openpyxl, xlsxwriter, reportlab).
    - Admin: django.contrib.admin plus core.admin customization.
    - Management commands: backup_db, scheduled_backup, createsu, setup_auto_backup, clear_cache, warm_cache, test_email.
    - Tests: Extensive suite in core/tests with module-per-feature organization; pytest is available, though README examples use manage.py test.

- Environment & configuration
  - .env.example documents the full set of environment variables used across features (DB, email, security, feature flags, backups, optional Redis/Sentry, etc.). Copy to .env for local development.
  - requirements.txt is the authoritative dependency set for dev/prod, including pytest/pytest-django, django-crontab, django-ratelimit, caching, export libs, and pip-audit. requirements_optimized.txt exists for slimmed prod builds (commented optional dev libs).

- Deployment (Render)
  - render.yaml / render_fixed.yaml define:
    - Web service: pip install + collectstatic during build; gunicorn for start.
    - postDeployCommand runs migrations and creates a superuser.
    - Provisioned Postgres database and env var wiring.
    - A separate cron service triggers python manage.py scheduled_backup daily at 17:00 UTC.

Notes for agents operating in this repo
- Prefer Python 3.11 locally to match pyproject and Render.
- When running tests, settings.py detects 'test' in sys.argv to simplify static files storage and disables rate limiting; no extra flags needed.
- If REDIS_URL is unset locally, caching defaults to local memory. Avoid assuming Redis features unless REDIS_URL is present.
- Some optional apps (cachalot, debug_toolbar) are conditionally enabled; code paths may differ in DEBUG vs production.
