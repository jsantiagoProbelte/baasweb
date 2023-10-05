from django.contrib import admin
# Register your models here.
from catalogue.models import Product, Vendor, RateUnit, Treatment

admin.site.register(Vendor)
admin.site.register(Product)
admin.site.register(RateUnit)
admin.site.register(Treatment)
