from django.urls import path

from . import views

urlpatterns = [
    path(
        'fieldtrials',
        views.FieldTrialListView.as_view(),
        name='fieldtrial-list'),
]
