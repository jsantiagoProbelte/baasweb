from django.urls import path
from . import recomender

urlpatterns = [
    # Field Trials urls
    path('recomender',
         recomender.RecomenderApi.as_view(),
         name='recomender'),
]
