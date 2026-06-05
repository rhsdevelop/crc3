"""
Development settings for the CRC project.
"""

from .settings_base import BASE_DIR
from .settings_base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'crc-rhsdoctors.pythonanywhere.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'origin': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'salao.db',
    },
}
