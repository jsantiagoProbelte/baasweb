from django.urls import path
from . import recomender, statsdata

urlpatterns = [
    # Field Trials urls
    path('recomender',
         recomender.RecomenderApi.as_view(),
         name='recomender'),
    path('statsdata',
         statsdata.StatsDataApi.as_view(),
         name='statsdata'),
]
