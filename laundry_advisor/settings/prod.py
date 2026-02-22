"""
Production settings for laundry_advisor project.
Deployed to Render. Completed in Plan 01-03.
"""

from .base import *
import dj_database_url

DEBUG = False

# Security — SECRET_KEY MUST be set as a Render environment variable
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = []

# Add Render external hostname dynamically
RENDER_EXTERNAL_HOSTNAME = env('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Database — PostgreSQL via DATABASE_URL (set automatically by Render Blueprint)
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files — WhiteNoise serves compressed/hashed static files
MIDDLEWARE.insert(
    MIDDLEWARE.index('django.middleware.security.SecurityMiddleware') + 1,
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# Tailwind CLI — do NOT auto-download in production (binary installed during build)
TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False

# Security headers for production (Render terminates TLS upstream)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
