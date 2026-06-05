"""
Production settings for PythonAnywhere.
"""

import os
from pathlib import Path

from .settings_base import *


def load_env_file(path):
    if not path.exists():
        return

    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line.removeprefix('export ').strip()
        if not line or line.startswith('#') or '=' not in line:
            continue

        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


for env_path in [
    BASE_DIR.parent / '.env',
    BASE_DIR / '.env',
    Path.home() / '.env',
    Path('/home/rhsdoctors/crc3/.env'),
    Path('/home/rhsdoctors/.env'),
]:
    load_env_file(env_path)


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


DEBUG = False

SECRET_KEY = env('CRC_SECRET_KEY')

ALLOWED_HOSTS = [
    'crc-rhsdoctors.pythonanywhere.com',
    'localhost',
]
ALLOWED_HOSTS += [
    host.strip()
    for host in os.environ.get('CRC_ALLOWED_HOSTS', '').split(',')
    if host.strip() and host.strip() not in ALLOWED_HOSTS
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
