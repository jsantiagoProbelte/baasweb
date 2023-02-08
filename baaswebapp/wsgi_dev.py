"""
WSGI config for baaswebapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""
# This file is to be able to launch the dev environment web app 
# from NGINX instead of python manage runserver
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')

application = get_wsgi_application()
