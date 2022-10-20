from django.urls import path
from . import views

urlpatterns = [
    path(
        'fieldtrials',
        views.FieldTrialListView.as_view(),
        name='fieldtrial-list'),
    path(
        'edit_fieldtrial',
        views.editNewFieldTrial,
        name='fieldtrial-edit'),
    path(
        'edit_fieldtrial/<int:field_trial_id>/',
        views.editNewFieldTrial,
        name='fieldtrial-edit'),
    path(
        'save_fieldtrial',
        views.saveFieldTrial,
        name='fieldtrial-save'),
]
