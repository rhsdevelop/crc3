"""
Environment selector for the CRC project.
"""

import os

from .settings_base import BASE_DIR


IS_PYTHONANYWHERE = (
    bool(os.environ.get('PYTHONANYWHERE_DOMAIN'))
    or str(BASE_DIR).startswith('/home/rhsdoctors/')
)
IS_PRODUCTION = os.environ.get('CRC_ENV') == 'production' or IS_PYTHONANYWHERE

if IS_PRODUCTION:
    from .settings_pa import *
else:
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
