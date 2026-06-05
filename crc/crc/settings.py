"""
Django settings for the CRC project.

This single settings module uses SQLite for local development and MySQL on
PythonAnywhere.
"""

import mimetypes
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

IS_PYTHONANYWHERE = (
    bool(os.environ.get('PYTHONANYWHERE_DOMAIN'))
    or str(BASE_DIR).startswith('/home/rhsdoctors/')
)
IS_PRODUCTION = os.environ.get('CRC_ENV') == 'production' or IS_PYTHONANYWHERE


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


if IS_PRODUCTION:
    SECRET_KEY = env('CRC_SECRET_KEY')
else:
    SECRET_KEY = env(
        'CRC_SECRET_KEY',
        'django-insecure-hji(93-)y42ovld755n#c(+8sj@7aef5*cx93oe%7o-9bjv($&',
    )

DEBUG = not IS_PRODUCTION

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'crc-rhsdoctors.pythonanywhere.com',
]
ALLOWED_HOSTS += [
    host.strip()
    for host in os.environ.get('CRC_ALLOWED_HOSTS', '').split(',')
    if host.strip() and host.strip() not in ALLOWED_HOSTS
]

INSTALLED_APPS = [
    'register.apps.RegisterConfig',
    'activities.apps.ActivitiesConfig',
    'meetings.apps.MeetingsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap4',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crc.wsgi.application'

if IS_PRODUCTION:
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
else:
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

origin_db = os.environ.get('CRC_ORIGIN_DB')
if origin_db:
    DATABASES['origin'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': origin_db,
    }

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

LANGUAGE_CODE = 'pt-BR'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = False

mimetypes.add_type('text/css', '.css', True)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = (BASE_DIR / 'static',)

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
