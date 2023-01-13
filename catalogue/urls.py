from django.urls import path
from . import product_views

urlpatterns = [
    # Field Trials urls
    path(
        'products',
        product_views.ProductListView.as_view(),
        name='product-list'),
    # path(
    #     'edit_fieldtrial',
    #     fieldtrial_views.editNewFieldTrial,
    #     name='fieldtrial-edit'),
    # path(
    #     'edit_fieldtrial/<int:field_trial_id>/',
    #     fieldtrial_views.editNewFieldTrial,
    #     name='fieldtrial-edit'),
    # path(
    #     'field_trial_api',
    #     fieldtrial_views.FieldTrialApi.as_view(),
    #     name='field_trial_api'),
    path(
        'product_api/<int:field_trial_id>/',
        product_views.ProductApi.as_view(),
        name='product_api'),
    # path(
    #     'save_fieldtrial',
    #     fieldtrial_views.saveFieldTrial,
    #     name='fieldtrial-save'),
]
