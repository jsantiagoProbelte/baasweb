from django.urls import path
from . import product_views

urlpatterns = [
    # Field Trials urls
    path('product/<int:product_id>/',
         product_views.ProductApi.as_view(),
         name='product_api'),
    path('product/add/', product_views.ProductCreateView.as_view(),
         name='product-add'),
    path('product/update/<int:pk>/', product_views.ProductUpdateView.as_view(),
         name='product-update'),
    path('product/delete/<int:pk>/', product_views.ProductDeleteView.as_view(),
         name='product-delete'),
    # Batch
    path('batch/<int:pk>/',
         product_views.BatchApi.as_view(),
         name='batch-api'),
    path('batch/add/<int:reference_id>/',
         product_views.BatchCreateView.as_view(),
         name='batch-add'),
    path('batch/update/<int:pk>/', product_views.BatchUpdateView.as_view(),
         name='batch-update'),
    path('batch/delete/<int:pk>/', product_views.BatchDeleteView.as_view(),
         name='batch-delete'),
    # Treatment
    path('treatment/<int:pk>/',
         product_views.TreatmentApi.as_view(),
         name='treatment-api'),
    path('treatment/add/<int:reference_id>/',
         product_views.TreatmentCreateView.as_view(),
         name='treatment-add'),
    path('treatment/update/<int:pk>/',
         product_views.TreatmentUpdateView.as_view(),
         name='treatment-update'),
    path('treatment/delete/<int:pk>/',
         product_views.TreatmentDeleteView.as_view(),
         name='treatment-delete'),
    # Product Variant
    path('product_variant/<int:pk>/',
         product_views.ProductVariantApi.as_view(),
         name='product_variant-api'),
    path('product_variant/add/<int:reference_id>/',
         product_views.ProductVariantCreateView.as_view(),
         name='product_variant-add'),
    path('product_variant/update/<int:pk>/',
         product_views.ProductVariantUpdateView.as_view(),
         name='product_variant-update'),
    path('product_variant/delete/<int:pk>/',
         product_views.ProductVariantDeleteView.as_view(),
         name='product_variant-delete')
]
