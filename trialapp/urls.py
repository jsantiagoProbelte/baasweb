from django.urls import path
from . import fieldtrial_views, thesis_views

urlpatterns = [
    path(
        'fieldtrials',
        fieldtrial_views.FieldTrialListView.as_view(),
        name='fieldtrial-list'),
    path(
        'edit_fieldtrial',
        fieldtrial_views.editNewFieldTrial,
        name='fieldtrial-edit'),
    path(
        'edit_fieldtrial/<int:field_trial_id>/',
        fieldtrial_views.editNewFieldTrial,
        name='fieldtrial-edit'),
    path(
        'save_fieldtrial',
        fieldtrial_views.saveFieldTrial,
        name='fieldtrial-save'),
    path(
        'thesislist/<int:field_trial_id>/',
        thesis_views.ThesisListView.as_view(),
        name='thesis-list'),
    path(
        'edit_thesis/<int:field_trial_id>/',
        thesis_views.editThesis,
        name='thesis-edit'),
    path(
        'edit_thesis/<int:field_trial_id>/<int:thesis_id>/',
        thesis_views.editThesis,
        name='thesis-edit'),
    path(
        'thesis-save',
        thesis_views.saveThesis,
        name='thesis-save'),
    path(
        'add_product_to_thesis_api',
        thesis_views.AddProductToThesis.as_view(),
        name='add_product_to_thesis_api')
]
