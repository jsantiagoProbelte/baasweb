from django.urls import path
from . import product_views

urlpatterns = [
    # Field Trials urls
    path('products',
         product_views.ProductListView.as_view(),
         name='product-list'),
    path('product_api/<int:product_id>/',
         product_views.ProductApi.as_view(),
         name='product_api'),
    path('product/add/', product_views.ProductCreateView.as_view(),
         name='product-add'),
    path('product/<int:pk>/', product_views.ProductUpdateView.as_view(),
         name='product-update'),
    path('product/delete/<int:pk>/', product_views.ProductDeleteView.as_view(),
         name='product-delete'),
]
