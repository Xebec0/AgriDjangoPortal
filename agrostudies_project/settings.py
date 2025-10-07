"""
Django settings for agrostudies_project project.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import dj_database_url
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allow hosts based on environment
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '0.0.0.0,localhost,127.0.0.1').split(',')
if not DEBUG:
    ALLOWED_HOSTS.append('agridjangoportal.onrender.com')
else:
    # Development hosts
    ALLOWED_HOSTS.extend(['97c4d0ce-8162-4751-a7b9-9bdc67fea09e-00-1fmmcvyer92ik.kirk.replit.dev', '.replit.dev'])

# CSRF Trusted Origins for secure form submissions
CSRF_TRUSTED_ORIGINS = [
    'https://agridjangoportal.onrender.com',
    'https://97c4d0ce-8162-4751-a7b9-9bdc67fea09e-00-1fmmcvyer92ik.kirk.replit.dev',
    'https://*.replit.dev',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1:50804',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',  # Our custom app
    'django_crontab',  # For scheduled tasks
]

# Add caching apps if available
try:
    import cachalot
    INSTALLED_APPS.append('cachalot')  # Automatic ORM caching
except ImportError:
    pass

# Add debug toolbar only in DEBUG mode
if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise middleware for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestContextMiddleware',
]

# Add debug toolbar middleware only in DEBUG mode
if DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

ROOT_URLCONF = 'agrostudies_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'agrostudies_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# Configure database using DATABASE_URL environment variable if available
# Uses SQLite locally if DATABASE_URL is not set
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,  # Connection lifetime in seconds
        conn_health_checks=True,  # Check connection before use
    )
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise configuration
# Use simpler storage for tests to avoid manifest issues
import sys
if 'test' in sys.argv:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # Cache static files for 1 year

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL used by @login_required redirects
# Points to a friendly prompt that opens the register/login modal
LOGIN_URL = 'auth_required'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Admin Registration
ADMIN_REGISTRATION_CODE = 'ADMIN123'

# ----- Email Configuration -----
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'merlielatosa@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'anrrwukmaiygowbb')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Agrostudies <noreply@agrostudies.com>')
EMAIL_TIMEOUT = 10  # Timeout in seconds

# For development/testing without email credentials, use console backend
if DEBUG and not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ----- Logging Configuration -----
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': LOG_LEVEL,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': LOG_LEVEL,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}

# ----- Cron Jobs Configuration -----
# Schedule automatic database backup at 5:00 PM (17:00) daily
CRONJOBS = [
    # Format: ('minute hour day month day_of_week', 'django_command')
    # Run backup at 5:00 PM (17:00) every day
    ('0 17 * * *', 'django.core.management.call_command', ['scheduled_backup']),
    
    # Alternative: Run backup every 6 hours for testing (uncomment if needed)
    # ('0 */6 * * *', 'django.core.management.call_command', ['scheduled_backup']),
]

# Crontab command prefix (for logging)
CRONTAB_COMMAND_PREFIX = 'DJANGO_SETTINGS_MODULE=agrostudies_project.settings'
CRONTAB_COMMAND_SUFFIX = '2>&1'

# ----- Production Security Settings -----
if not DEBUG:
    # HTTPS/SSL Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Security Headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # HSTS Settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ----- Rate Limiting Configuration -----
# Disable rate limiting during tests to avoid false failures
RATELIMIT_ENABLE = 'test' not in sys.argv

# ----- Caching Configuration -----
REDIS_URL = os.getenv('REDIS_URL', '')

# Use Redis if available, otherwise fallback to local memory cache
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                }
            },
            'KEY_PREFIX': 'agrostudies',
            'VERSION': 1,
            'TIMEOUT': 300,  # 5 minutes default
        }
    }
    # Session caching (faster than database sessions)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # Fallback to local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'agrostudies-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

SESSION_COOKIE_AGE = 86400  # 24 hours

# Cache time to live settings
CACHE_TTL = {
    'default': 300,      # 5 minutes
    'programs': 600,     # 10 minutes  
    'candidates': 300,   # 5 minutes
    'user_data': 900,    # 15 minutes
    'static_content': 3600,  # 1 hour
}

# ----- Sentry Error Tracking -----
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        send_default_pii=False,  # Don't send personally identifiable information
        environment='production' if not DEBUG else 'development',
    )
