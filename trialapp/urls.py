from django.urls import path
from . import assessment_views, fieldtrial_views, thesis_views, data_views, \
    application_views, filter_helpers, trial_views
import baaswebapp.meteo_api as meteo_api

urlpatterns = [
    # Field Trials urls
    path(
        'trials',
        filter_helpers.TrialListView.as_view(),
        name='trial-list'),
    path('products',
         filter_helpers.ProductListView.as_view(),
         name='product-list'),
    path(
        'crops',
        filter_helpers.CropListView.as_view(),
        name='crop-list'),
    path(
        'fieldtrials',
        fieldtrial_views.FieldTrialListView.as_view(),
        name='fieldtrial-list'),
    path('fieldtrial/add/',
         fieldtrial_views.FieldTrialCreateView.as_view(),
         name='fieldtrial-add'),
    path('fieldtrial/edit/<int:pk>/',
         fieldtrial_views.FieldTrialUpdateView.as_view(),
         name='fieldtrial-update'),
    path(
        'fieldtrial_api/<int:pk>/',
        fieldtrial_views.FieldTrialApi.as_view(),
        name='fieldtrial_api'),
    path(
        'trial_api/<int:pk>/',
        trial_views.TrialApi.as_view(),
        name='trial_api'),
    path(
        'trial_content_api',
        trial_views.trialContentApi,
        name='trial-content-api'),
    path(
        'fieldtrial/delete/<int:pk>/',
        fieldtrial_views.FieldTrialDeleteView.as_view(),
        name='fieldtrial-delete'),
    path(
        'download_pdf/<int:pk>/',
        fieldtrial_views.DownloadTrial.as_view(),
        name='download_pdf'),
    # Thesis urls
    path(
        'thesislist/<int:field_trial_id>/',
        thesis_views.ThesisListView.as_view(),
        name='thesis-list'),
    path('thesis_api/<int:pk>/',
         thesis_views.ThesisApi.as_view(),
         name='thesis_api'),
    path('thesis/add/<int:field_trial_id>/',
         thesis_views.ThesisCreateView.as_view(),
         name='thesis-add'),
    path('thesis/edit/<int:pk>/', thesis_views.ThesisUpdateView.as_view(),
         name='thesis-update'),
    path(
        'thesis/delete/<int:pk>/',
        thesis_views.ThesisDeleteView.as_view(),
        name='thesis-delete'),
    path(
        'set_replica_position/<int:x>/<int:y>/<int:oldReplicaId>/',
        thesis_views.SetReplicaPosition.as_view(),
        name='set-replica-position'),
    # treatment in thesis
    path('treatment_thesis/add/<int:thesis_id>/',
         thesis_views.TreatmentThesisSetView.as_view(),
         name='treatment_thesis-add'),
    path('treatment_thesis/delete/<int:pk>/',
         thesis_views.TreatmentThesisDeleteView.as_view(),
         name='treatment_thesis-delete'),
    # Assessment urls
    path(
        'assessment/<int:pk>/',
        assessment_views.AssessmentView.as_view(),
        name='assessment'),
    path(
        'assessment_list/<int:field_trial_id>/',
        assessment_views.AssessmentListView.as_view(),
        name='assessment-list'),
    path('assessment/add/<int:field_trial_id>/',
         assessment_views.AssessmentCreateView.as_view(),
         name='assessment-add'),
    path('assessment/edit/<int:pk>/',
         assessment_views.AssessmentUpdateView.as_view(),
         name='assessment-update'),
    path(
        'assessment/delete/<int:pk>/',
        assessment_views.AssessmentDeleteView.as_view(),
        name='assessment-delete'),
    path(
        'assessment_api',
        assessment_views.AssessmentApi.as_view(),
        name='assessment_api'),
    # Data & measurements apis
    path(
        'set_data_point',
        data_views.SetDataAssessment.as_view(),
        name='set_data_point'),
    path(
        'trial_data/<int:pk>/',
        data_views.TrialDataApi.as_view(),
        name='trial_data'),
    # Application urls
    path(
        'applicationlist/<int:field_trial_id>/',
        application_views.ApplicationListView.as_view(),
        name='application-list'),
    path('application/<int:pk>/',
         application_views.ApplicationApi.as_view(),
         name='application_api'),
    path('application/add/<int:field_trial_id>/',
         application_views.ApplicationCreateView.as_view(),
         name='application-add'),
    path('application/edit/<int:pk>/',
         application_views.ApplicationUpdateView.as_view(),
         name='application-update'),
    path(
        'application/delete/<int:pk>/',
        application_views.ApplicationDeleteView.as_view(),
        name='application-delete'),
    # Meteo API
    path(
        'meteo_api/<int:field_trial_id>/',
        meteo_api.MeteoApi.as_view(),
        name='meteo_api'),
    # BaaS-Views
    path('baasview', filter_helpers.BaaSView.as_view(), name='baasview')


]
