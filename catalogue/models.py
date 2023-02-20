from django.db import models
from baaswebapp.models import ModelHelpers


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ProductCategory(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class RateUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Product(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE,
                                 null=True)

    def get_absolute_url(self):
        return "/product_api/%i/" % self.id


class ProductVariant(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return self.product.get_absolute_url()


class Batch(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return self.product.get_absolute_url()


class Treatment(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return self.product.get_absolute_url()
