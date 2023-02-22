from django.urls import path
from . import assessment_views, fieldtrial_views, thesis_views, data_views

urlpatterns = [
    # Field Trials urls
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
        'fieldtrial_api/<int:field_trial_id>/',
        fieldtrial_views.FieldTrialApi.as_view(),
        name='fieldtrial_api'),
    path(
        'fieldtrial/delete/<int:pk>/',
        fieldtrial_views.FieldTrialDeleteView.as_view(),
        name='fieldtrial-delete'),
    path(
        'reshuffle_blocks/<int:field_trial_id>/',
        fieldtrial_views.reshuffle_blocks,
        name='reshuffle-blocks'),
    # Thesis urls
    path(
        'thesislist/<int:field_trial_id>/',
        thesis_views.ThesisListView.as_view(),
        name='thesis-list'),
    path('thesis_api/<int:thesis_id>/',
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
        'manage_product_to_thesis_api',
        thesis_views.ManageProductToThesis.as_view(),
        name='manage_product_to_thesis_api'),
    path(
        'manage_replica_to_thesis_api',
        thesis_views.ManageReplicaToThesis.as_view(),
        name='manage_replica_to_thesis_api'),
    # Evaluation urls
    path(
        'assessment_api/<int:evaluation_id>/',
        assessment_views.AssessmentApi.as_view(),
        name='assessment_api'),
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
    # Data & measurements apis
    path(
        'trial_assessment_set_list/<int:field_trial_id>/',
        data_views.showTrialAssessmentSetIndex,
        name='trial-assessment-set-list'),
    path(
        'manage_trial_assessment_set_api',
        data_views.ManageTrialAssessmentSet.as_view(),
        name='manage_trial_assessment_set_api'),
    path(
        'set_data_point',
        data_views.SetDataEvaluation.as_view(),
        name='set_data_point')]
