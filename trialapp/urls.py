from django.urls import path
from . import fieldtrial_views, thesis_views, application_views

urlpatterns = [
    # Field Trials urls
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
        'show_fieldtrial/<int:field_trial_id>/',
        fieldtrial_views.showFieldTrial,
        name='fieldtrial-show'),
    path(
        'save_fieldtrial',
        fieldtrial_views.saveFieldTrial,
        name='fieldtrial-save'),
    # Thesis urls
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
        'save_thesis',
        thesis_views.saveThesis,
        name='thesis-save'),
    path(
        'manage_product_to_thesis_api',
        thesis_views.ManageProductToThesis.as_view(),
        name='manage_product_to_thesis_api'),
    path(
        'manage_replica_to_thesis_api',
        thesis_views.ManageReplicaToThesis.as_view(),
        name='manage_replica_to_thesis_api'),
    # Application urls
    path(
        'applicationlist/<int:field_trial_id>/',
        application_views.ApplicationListView.as_view(),
        name='application-list'),
    path(
        'edit_application/<int:field_trial_id>/',
        application_views.editApplication,
        name='application-edit'),
    path(
        'edit_application/<int:field_trial_id>/<int:application_id>/',
        application_views.editApplication,
        name='application-edit'),
    path(
        'save_application',
        application_views.saveApplication,
        name='application-save'),
    path(
        'manage_product_to_application_api',
        application_views.ManageProductToApplication.as_view(),
        name='manage_product_to_application_api')
]
