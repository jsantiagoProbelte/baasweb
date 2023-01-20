from django.contrib import admin
# Register your models here.
from catalogue.models import Product, Vendor, ProductCategory

admin.site.register(Product)
admin.site.register(Vendor)
admin.site.register(ProductCategory)
