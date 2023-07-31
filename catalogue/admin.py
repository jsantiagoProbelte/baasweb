from django.contrib import admin
# Register your models here.
from catalogue.models import Product, Vendor, ProductCategory, RateUnit, \
    Batch, ProductVariant, Treatment

admin.site.register(Vendor)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Batch)
admin.site.register(RateUnit)
admin.site.register(Treatment)
