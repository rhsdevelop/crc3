"""
Production settings for PythonAnywhere.
"""

import os

from .settings_base import *


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


DEBUG = False

SECRET_KEY = env('CRC_SECRET_KEY')

ALLOWED_HOSTS = [
    host.strip()
    for host in env('CRC_ALLOWED_HOSTS', 'crc-rhsdoctors.pythonanywhere.com').split(',')
    if host.strip()
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('CRC_DB_NAME', 'rhsdoctors$crc'),
        'USER': env('CRC_DB_USER', 'rhsdoctors'),
        'PASSWORD': env('CRC_DB_PASSWORD'),
        'HOST': env('CRC_DB_HOST', 'rhsdoctors.mysql.pythonanywhere-services.com'),
        'PORT': env('CRC_DB_PORT', '3306'),
    },
}

origin_db = os.environ.get('CRC_ORIGIN_DB')
if origin_db:
    DATABASES['origin'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': origin_db,
    }
