# Connect to a server using the ssh keys.
# See the sshtunnel documentation for using password authentication
# # python manage.py migrate --database=shhtunnel_db
# # python remote_prod_manage.py shell
# # from trialapp.models import TrialDbInitialLoader
# # TrialDbInitialLoader.loadInitialTrialValues(location='shhtunnel_db')
from baaswebapp.settings import *  # noqa: F403, F401
from sshtunnel import SSHTunnelForwarder
from keymanager import KeyManager

keymanager = KeyManager()
DEBUG = True
SECRET_KEY = keymanager.get_secret("DJANGO-SECRET-KEY")
VPIP = keymanager.get_secret("VPIP")
VPUSERNAME = keymanager.get_secret("VP-USER")
ssh_tunnel = SSHTunnelForwarder(
    VPIP,
    ssh_private_key='../keys/'
                    'baas-db-server-connect_key.cer',
    ssh_username=VPUSERNAME,
    remote_bind_address=('baasweb-server.postgres.database.azure.com', 5432),
)
ssh_tunnel.start()
TRIALS_ARCHIVE = 'TEAMS'

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1',
        'PORT': ssh_tunnel.local_bind_port,
        'NAME': keymanager.get_secret("DB-NAME"),
        'USER': keymanager.get_secret("DB-SUPER-USER"),
        'PASSWORD': keymanager.get_secret("DB-SUPER-PASS")
    }
}
