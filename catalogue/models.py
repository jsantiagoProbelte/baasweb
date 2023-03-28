from django.db import models
from baaswebapp.models import ModelHelpers

DEFAULT = 'default'
UNTREATED = 'Untreated'


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ProductCategory(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class RateUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)

    @classmethod
    def getDefault(cls):
        return RateUnit.objects.get(name=DEFAULT)


class Product(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE,
                                 null=True)

    def get_absolute_url(self):
        return "/product/%i/" % self.id


class ProductVariant(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return "/product_variant/%i/" % self.id

    @classmethod
    def getItems(cls, product):
        return ProductVariant.objects.filter(product=product).order_by('name')

    @classmethod
    def createDefault(cls, product):
        return cls.objects.create(
            product=product, name=DEFAULT + ' variant',
            description=DEFAULT + 'variant for' + product.name)


class Batch(ModelHelpers, models.Model):
    name = models.CharField(max_length=100, null=True)
    serial_number = models.CharField(max_length=100, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant,
                                        on_delete=models.CASCADE)

    @classmethod
    def getItems(cls, product):
        return Batch.objects.filter(
            product_variant__product=product).order_by('name')

    def get_absolute_url(self):
        return "/batch/%i/" % self.id

    @classmethod
    def createDefault(cls, variant):
        name = DEFAULT + ' batch for ' + variant.name

        return cls.objects.create(
            product_variant=variant, rate=0,
            rate_unit=RateUnit.getDefault(),
            name=name)


class Treatment(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)

    @classmethod
    def getItems(cls, product):
        return Treatment.objects.filter(
            batch__product_variant__product=product).order_by('name')

    @classmethod
    def displayItems(cls, product):
        display = []
        for item in cls.getItems(product):
            display.append({'name': item.getName(short=True),
                            'id': item.id})
        return display

    def get_absolute_url(self):
        return "/treatment/%i/" % self.id

    def getName(self, short=False):
        if self.name:
            return self.name
        else:
            productName = ''
            if not short:
                productName = self.batch.product_variant.product.name
            varianName = self.batch.product_variant.name
            if DEFAULT in varianName:
                varianName = ''
            rateUnitName = '{} {}'.format(self.rate, self.rate_unit.name)
            batchName = self.batch.name
            if not short and DEFAULT in batchName:
                batchName = ''
            return '{} {} {} {}'.format(
                   productName,
                   varianName,
                   batchName,
                   rateUnitName)
