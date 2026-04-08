"""
Development settings for laundry_advisor project.
Uses SQLite, DEBUG=True, and relaxed security settings.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Media files — served locally in development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
