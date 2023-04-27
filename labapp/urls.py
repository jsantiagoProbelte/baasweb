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
    path('labtrial/delete/<int:pk>/',
         labtrial_views.LabTrialDeleteView.as_view(),
         name='labtrial-delete'),
    path('labtrial/<int:pk>/',
         labtrial_views.LabTrialView.as_view(),
         name='labtrial-show'),
    # Data & measurements apis
    path(
        'set_data_point_lab',
        labtrial_views.SetLabDataPoint.as_view(),
        name='set_data_point_lab'),
    path(
        'set_thesis_name',
        labtrial_views.SetLabThesis.as_view(),
        name='set_thesis_name'),
]
