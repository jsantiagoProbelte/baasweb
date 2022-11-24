from django.urls import path
from . import fieldtrial_views, thesis_views, evaluation_views,\
              data_views

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
        'field_trial_api',
        fieldtrial_views.FieldTrialApi.as_view(),
        name='field_trial_api'),
    path(
        'field_trial_api/<int:field_trial_id>/',
        fieldtrial_views.FieldTrialApi.as_view(),
        name='field_trial_api'),
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
        'thesis_api',
        thesis_views.ThesisApi.as_view(),
        name='thesis_api'),
    path(
        'thesis_api/<int:thesis_id>/',
        thesis_views.ThesisApi.as_view(),
        name='thesis_api'),
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
    # Evaluation urls
    path(
        'assessment_api',
        evaluation_views.AssessmentApi.as_view(),
        name='assessment_api'),
    path(
        'evaluationlist/<int:field_trial_id>/',
        evaluation_views.EvaluationListView.as_view(),
        name='evaluation-list'),
    path(
        'edit_evaluation/<int:field_trial_id>/',
        evaluation_views.editEvaluation,
        name='evaluation-edit'),
    path(
        'edit_evaluation/<int:field_trial_id>/<int:evaluation_id>/',
        evaluation_views.editEvaluation,
        name='evaluation-edit'),
    path(
        'save_evaluation',
        evaluation_views.saveEvaluation,
        name='evaluation-save'),
    path(
        'manage_product_to_evaluation_api',
        evaluation_views.ManageProductToEvaluation.as_view(),
        name='manage_product_to_evaluation_api'),
    # Data & measurements apis
    path(
        'trial_assessment_set_list/<int:field_trial_id>/',
        data_views.showTrialAssessmentSetIndex,
        name='trial-assessment-set-list'),
    path(
        'data_thesis_index/<int:evaluation_id>/',
        data_views.showDataThesisIndex,
        name='data_thesis_index'),
    path(
        'data_replica_index/<int:evaluation_id>/',
        data_views.showDataReplicaIndex,
        name='data_replica_index'),
    path(
        'manage_trial_assessment_set_api',
        data_views.ManageTrialAssessmentSet.as_view(),
        name='manage_trial_assessment_set_api'),
    path(
        'set_data_point',
        data_views.SetDataEvaluation.as_view(),
        name='set_data_point'),
    # path(
    #     'add_data_thesis/<int:thesis_id>/<int:evaluation_id>/',
    #     data_views.add_data_thesis,
    #     name='show-data-options'),
    # path(
    #     'add_data_replica/<int:replica_id>/<int:evaluation_id>/',
    #     data_views.add_data_replica,
    #     name='show-data-options'),
]
