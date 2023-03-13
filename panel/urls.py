from django.urls import path
from . import recomender, statsdata, quality_panel

urlpatterns = [
    # Field Trials urls
    path('recomender',
         recomender.RecomenderApi.as_view(),
         name='recomender'),
    path('statsdata',
         statsdata.StatsDataApi.as_view(),
         name='statsdata'),
    path('thesis_quality_panel',
         quality_panel.ThesisPanelApi.as_view(),
         name='thesis_quality_panel'),
]
