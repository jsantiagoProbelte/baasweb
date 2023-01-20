from django.db import models
from baaswebapp.models import ModelHelpers


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ProductCategory(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Product(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE,
                                 null=True)

    def get_absolute_url(self):
        return "/product_api/%i/" % self.id
