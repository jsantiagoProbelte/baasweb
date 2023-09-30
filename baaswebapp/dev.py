# from baaswebapp import settings
# We need to import all the settings, but flake does not like,
# do we explicitly ignore this errors
from baaswebapp.settings import *  # noqa: F403, F401

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_baaswebapp.sqlite3',
    }
}

TRIALS_ARCHIVE = 'LOCAL'
KEYVAULT_URL = 'blabla'
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'db_baas',
#         'USER': 'admin_baas',
#         'PASSWORD': 'B@@SisGreat',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
FIDO_SERVER_ID = "localhost"
