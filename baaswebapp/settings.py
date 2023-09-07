"""
Django settings for baaswebapp project.

Specific for development are in dev.py and for production in prod.py

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import django_extensions
from pathlib import Path
from dotenv import load_dotenv
from dotenv import load_dotenv
import os
import logging.config
from django.utils.translation import gettext_lazy as _
import passkeys
from keymanager import KeyManager
# Load local .env environment variables
load_dotenv()

keymanager = KeyManager()
# Load local .env environment variables
load_dotenv()

keymanager = KeyManager()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# STATIC_ROOT definition is moved to dev.py or prod.py

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-t78nwv1+tehfr27dg2jq!$!(!1k3bt2@vw98r37$2r=c3!9+)7'
SENDGRID_KEY = keymanager.get_secret("SENDGRID-KEY")

# SECURITY WARNING: don't run with debug turned on in production!

AUTHENTICATION_BACKENDS = [
    'sesame.backends.ModelBackend', 'passkeys.backend.PasskeyModelBackend']
KEY_ATTACHMENT = passkeys.Attachment.PLATFORM
# Server rp id for FIDO2, it the full domain of your project
FIDO_SERVER_ID = "localhost"
FIDO_SERVER_NAME = "BaasWebApp"

ALLOWED_HOSTS = ['*']


# Application definition
BASE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize'
]

EXTENDED_APPS = [
    'crispy_forms',
    'bootstrap5',
    'rest_framework',
    'widget_tweaks',
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'passkeys',
    'django_extensions',
    'rest_framework.authtoken',
    'drfpasswordless',
]

CUSTOM_APPS = [
    'baaswebapp',
    'trialapp',
    'catalogue',
    'panel',
    'labapp'
]

INSTALLED_APPS = BASE_APPS + EXTENDED_APPS + CUSTOM_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_plotly_dash.middleware.BaseMiddleware',

]

ROOT_URLCONF = 'baaswebapp.urls'

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

WSGI_APPLICATION = 'baaswebapp.wsgi.application'
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
# Databases are defined in dev.py or prod.py


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

DJANGO_CONTRIB = 'django.contrib.auth.password_validation.'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': DJANGO_CONTRIB + 'UserAttributeSimilarityValidator',
    },
    {
        'NAME': DJANGO_CONTRIB + 'MinimumLengthValidator',
    },
    {
        'NAME': DJANGO_CONTRIB + 'CommonPasswordValidator',
    },
    {
        'NAME': DJANGO_CONTRIB + 'NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGES = [
    ('en', _('English')),
    ('es', _('Spanish')),
    # Add more languages as needed.
]

LANGUAGE_CODE = 'es'

LOCALE_PATHS = ('locale',)

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/login'

# Logging Configuration

# Clear prev config
LOGGING_CONFIG = None

# Get loglevel from env
LOGLEVEL = os.getenv('DJANGO_LOGLEVEL', 'info').upper()

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format':
                '%(asctime)s %(levelname)s '
                '[%(name)s:%(lineno)s] '
                '%(module)s %(process)d %(thread)d %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        '': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
        },
    },
})

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        'rest_framework.authentication.TokenAuthentication',
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ]
}

X_FRAME_OPTIONS = 'SAMEORIGIN'
