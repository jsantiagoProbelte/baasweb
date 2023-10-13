from django.db import models
from baaswebapp.models import ModelHelpers, PType, Category
from django.utils.translation import gettext_lazy as _

DEFAULT = 'default'
UNTREATED = 'Untreated'


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    key_vendor = models.BooleanField(default=False)


class RateUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)

    @classmethod
    def getDefault(cls):
        return RateUnit.objects.get(name=DEFAULT)


class Product(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True)
    active_substance = models.CharField(max_length=100, null=True)

    # Product Basics
    pest_disease = models.CharField(max_length=100, null=True)
    concentration = models.CharField(max_length=100, null=True)
    ph = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    presentation = models.CharField(max_length=100, null=True)
    application = models.CharField(max_length=100, null=True)
    weather_temperature = models.IntegerField(null=True)
    weather_humidity = models.IntegerField(null=True)
    security_period = models.CharField(max_length=100, null=True)
    mixes = models.CharField(max_length=100, null=True)

    img_link = models.URLField(max_length=300, null=True)
    description = models.TextField(null=True)

    purpose = models.CharField(max_length=100, null=True)

    type_product = models.CharField(
        max_length=3,
        choices=PType.choices,
        default=PType.UNKNOWN)

    biological = models.BooleanField(default=False)

    def get_absolute_url(self):
        return f"/product/{self.id}/"

    def nameType(self):
        bio = 'Bio' if self.biological else ''

        if not self.type_product:
            name = PType.UNKNOWN
        else:
            name = self.get_type_product_display()
        return bio + _(name)

    def category(self):
        return Product.getCategory(self.type_product)

    @staticmethod
    def getCategory(type_product):
        if not type_product:
            return Category.UNKNOWN
        if type_product in [PType.FERTILIZER]:
            return Category.NUTRITIONAL
        elif type_product in [
                PType.HERBICIDE, PType.INSECTICIDE,
                PType.NEMATICIDE, PType.FUNGICIDE]:
            return Category.CONTROL
        elif type_product == PType.ESTIMULANT:
            return Category.ESTIMULANT
        else:
            return Category.UNKNOWN


class Treatment(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)

    @classmethod
    def getItems(cls, product):
        treats = Treatment.objects.filter(product=product) if product \
                 else Treatment.objects.all()
        return treats.order_by('rate_unit__name', 'rate')

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
        productName = ''
        if not short:
            productName = '' if self.product is None else self.product.name
        rateUnitName = '{} {}'.format(self.rate, self.rate_unit.name)

        return '{} {} {}'.format(productName, rateUnitName, self.name)

    def getDosis(self):
        return {'rate': self.rate, 'unit': self.rate_unit.name}
