"""baaswebapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from baaswebapp import views
from django.conf.urls.static import static
from django.conf import settings
from sesame.views import LoginView
from trialapp import filter_helpers
admin.autodiscover()

urlpatterns = [
    path('', filter_helpers.ProductListView.as_view(), name='home'),
    path('hidden_home', views.home, name='hidden-home'),
    path('baaswebapp_index', views.baaswebapp_index, name='baaswebapp_index'),
    path("sesame/login/", LoginView.as_view(), name="sesame-login"),
    path('', views.home, name='home'),
    re_path(r'^passkeys/', include('passkeys.urls')),
    path('', include('trialapp.urls')),
    path('', include('catalogue.urls')),
    path('', include('panel.urls')),
    path('', include('labapp.urls')),
    path("logout", views.logout_request, name="logout"),
    path("login", views.login_request_passkey, name="login"),
    path("login_email", views.login_email, name="login_email"),
    path('', include('drfpasswordless.urls')),

    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
]

urlpatterns += staticfiles_urlpatterns() +\
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + \
    static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
