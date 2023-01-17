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
