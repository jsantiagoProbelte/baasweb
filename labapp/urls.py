from django.urls import path
from . import labtrial_views

urlpatterns = [
    # Field Trials urls
    path(
        'labtrials',
        labtrial_views.LabTrialListView.as_view(),
        name='labtrial-list'),
    path('labtrial/add/',
         labtrial_views.LabTrialCreateView.as_view(),
         name='labtrial-add'),
    path('labtrial/edit/<int:pk>/',
         labtrial_views.LabTrialUpdateView.as_view(),
         name='labtrial-update'),
]
