# We need to import all the settings, but flake does not like,
# do we explicitly ignore this errors
from baaswebapp.settings import *  # noqa: F403, F401
DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'baas_db',
        'USER': 'baas_admin',
        'PASSWORD': 'b2@s_r#cks',
        'HOST': 'baasweb-server.postgres.database.azure.com',
        'PORT': '5432',
    }
}
CSRF_TRUSTED_ORIGINS = ['https://baasweb.azurewebsites.net']
