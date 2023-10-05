from django.urls import path
from . import product_views

urlpatterns = [
    # Field Trials urls
    path('product/<int:pk>/',
         product_views.ProductApi.as_view(),
         name='product_api'),
    path('product/add/', product_views.ProductCreateView.as_view(),
         name='product-add'),
    path('product/update/<int:pk>/', product_views.ProductUpdateView.as_view(),
         name='product-update'),
    path('product/delete/<int:pk>/', product_views.ProductDeleteView.as_view(),
         name='product-delete'),
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
]
