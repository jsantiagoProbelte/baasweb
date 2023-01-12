# from baaswebapp import settings
# We need to import all the settings, but flake does not like,
# do we explicitly ignore this errors
from baaswebapp.settings import *  # noqa: F403, F401

# Connect to a server using the ssh keys.
# See the sshtunnel documentation for using password authentication
# # python manage.py migrate --database=shhtunnel_db
# # python manage.py shell
# # from trialapp.models import TrialDbInitialLoader
# # TrialDbInitialLoader.loadInitialTrialValues(location='shhtunnel_db')

# from sshtunnel import SSHTunnelForwarder
# ssh_tunnel = SSHTunnelForwarder(
#     '51.137.115.231',
#     ssh_private_key='/Users/jsantiago/Code/azure/baasweb_server/'
#                     'baas-server-connect-vm_key.cer',
#     ssh_username='azureuser',
#     remote_bind_address=('baasweb-server.postgres.database.azure.com', 5432),
# )
# ssh_tunnel.start()

DEBUG = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db_baaswebapp.sqlite3',
    },
    # 'shhtunnel_db': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'HOST': '127.0.0.1',
    #     'PORT': ssh_tunnel.local_bind_port,
    #     'NAME': 'baas_db',
    #     'USER': 'ugeudpboxa',
    #     'PASSWORD': '3O760T1N7725FZE0$',
    # },
}
