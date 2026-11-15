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

RENDER_EXTERNAL_HOSTNAME = env('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

EC2_HOST = env('EC2_HOST', default=None)
if EC2_HOST:
    ALLOWED_HOSTS.append(EC2_HOST)

# Custom domain served over HTTPS by nginx + Let's Encrypt (set via Ansible).
DOMAIN = env('DOMAIN', default='')
if DOMAIN:
    ALLOWED_HOSTS += [DOMAIN, f'www.{DOMAIN}']
    CSRF_TRUSTED_ORIGINS = [f'https://{DOMAIN}', f'https://www.{DOMAIN}']

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

# S3 media storage — extends STORAGES without replacing the WhiteNoise staticfiles entry
STORAGES["default"] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {
        "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
        "region_name": env("AWS_S3_REGION_NAME", default="us-east-1"),
        "access_key": env("AWS_ACCESS_KEY_ID"),
        "secret_key": env("AWS_SECRET_ACCESS_KEY"),
        "querystring_auth": False,
        "file_overwrite": True,
        "default_acl": None,
    },
}

# Tailwind CLI — do NOT auto-download in production (binary installed during build)
TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False

# HTTPS: always on Render; on EC2 only once a DOMAIN (and so a TLS cert) is configured.
HTTPS_ENABLED = bool(DOMAIN) or not bool(EC2_HOST)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if HTTPS_ENABLED else None
SESSION_COOKIE_SECURE = HTTPS_ENABLED
CSRF_COOKIE_SECURE = HTTPS_ENABLED
SECURE_SSL_REDIRECT = HTTPS_ENABLED
# HSTS makes browsers refuse plain HTTP for this long — start short (1 day) on a
# fresh setup; raise HSTS_SECONDS to 31536000 once HTTPS has proven stable.
SECURE_HSTS_SECONDS = env.int('HSTS_SECONDS', default=86400) if HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
