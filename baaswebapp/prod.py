# We need to import all the settings, but flake does not like,
# do we explicitly ignore this errors
from baaswebapp.settings import *  # noqa: F403, F401
from keymanager import KeyManager

keymanager = KeyManager()
DEBUG = True
SECRET_KEY = keymanager.get_secret("DJANGO-SECRET-KEY")
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': keymanager.get_secret("DB-NAME"),
        'USER': keymanager.get_secret("DB-USER"),
        'PASSWORD': keymanager.get_secret("DB-PASS"),
        'HOST': keymanager.get_secret("DB-HOST"),
        'PORT': '5432',
    }
}
CSRF_TRUSTED_ORIGINS = ['https://baasweb.azurewebsites.net']

TRIALS_ARCHIVE = 'TEAMS'
FIDO_SERVER_ID = "baasweb.azurewebsites.net"
