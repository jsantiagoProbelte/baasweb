from django.db import models
from baaswebapp.models import ModelHelpers
import urllib.parse
import requests
from datetime import datetime, timedelta

DEFAULT = 'default'
UNTREATED = 'Untreated'


class Weather(ModelHelpers, models.Model):
    date = models.DateField()
    recent = models.BooleanField()
    latitude = models.DecimalField(decimal_places=20, max_digits=100)
    longitude = models.DecimalField(decimal_places=15, max_digits=100)

    max_temp = models.DecimalField(decimal_places=5, max_digits=100)
    min_temp = models.DecimalField(decimal_places=5, max_digits=100)
    mean_temp = models.DecimalField(decimal_places=5, max_digits=100)

    soil_temp_0_to_7cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_temp_7_to_28cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_temp_28_to_100cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_temp_100_to_255cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)

    soil_moist_0_to_7cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_moist_7_to_28cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_moist_28_to_100cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    soil_moist_100_to_255cm = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    dew_point = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)
    relative_humidity = models.DecimalField(
        decimal_places=2, max_digits=100, null=True, default=None)

    precipitation = models.DecimalField(decimal_places=5, max_digits=100)
    precipitation_hours = models.DecimalField(
        decimal_places=5, max_digits=100)
    max_wind_speed = models.DecimalField(decimal_places=5, max_digits=100)

    def fetchWeather(self):
        url = 'https://archive-api.open-meteo.com/v1/archive?daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours,windspeed_10m_max&timezone=auto&'
        if self.date > (datetime.now() - timedelta(days=7)).date():
            url = 'https://api.open-meteo.com/v1/forecast?daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours,windspeed_10m_max&timezone=auto&'
            self.recent = True
        else:
            self.fetchWeatherHourly()
            self.recent = False

        params = {'latitude': self.latitude,
                  'longitude': self.longitude,
                  'start_date': self.date,
                  'end_date': self.date}
        url += (urllib.parse.urlencode(params))
        res = requests.get(url)
        res.raise_for_status()
        weather = res.json()['daily']

        self.max_temp, self.min_temp = weather[
            'temperature_2m_max'][0], weather['temperature_2m_min'][0]
        self.mean_temp = (self.max_temp + self.min_temp) / 2
        self.precipitation, self.precipitation_hours = weather[
            'precipitation_sum'][0], weather['precipitation_hours'][0]
        self.max_wind_speed = weather['windspeed_10m_max'][0]

    def fetchWeatherHourly(self):
        url = 'https://archive-api.open-meteo.com/v1/archive?hourly=soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,soil_temperature_28_to_100cm,soil_temperature_100_to_255cm,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,relativehumidity_2m,dewpoint_2m&timezone=auto&'
        params = {'latitude': self.latitude,
                  'longitude': self.longitude,
                  'start_date': self.date,
                  'end_date': self.date}
        url += (urllib.parse.urlencode(params))
        res = requests.get(url)
        res.raise_for_status()
        weather = res.json()['hourly']
        self.assignHourlyToAverage(weather)

    def assignHourlyToAverage(self, weather):
        self.soil_temp_0_to_7cm = sum(
            weather['soil_temperature_0_to_7cm']) / len(weather['soil_temperature_0_to_7cm'])
        self.soil_temp_7_to_28cm = sum(
            weather['soil_temperature_7_to_28cm']) / len(weather['soil_temperature_7_to_28cm'])
        self.soil_temp_28_to_100cm = sum(
            weather['soil_temperature_28_to_100cm']) / len(weather['soil_temperature_28_to_100cm'])
        self.soil_temp_100_to_255cm = sum(
            weather['soil_temperature_100_to_255cm']) / len(weather['soil_temperature_100_to_255cm'])

        self.soil_moist_0_to_7cm = sum(
            weather['soil_moisture_0_to_7cm']) / len(weather['soil_moisture_0_to_7cm'])
        self.soil_moist_7_to_28cm = sum(
            weather['soil_moisture_7_to_28cm']) / len(weather['soil_moisture_7_to_28cm'])
        self.soil_moist_28_to_100cm = sum(
            weather['soil_moisture_28_to_100cm']) / len(weather['soil_moisture_28_to_100cm'])
        self.soil_moist_100_to_255cm = sum(
            weather['soil_moisture_100_to_255cm']) / len(weather['soil_moisture_100_to_255cm'])
        self.relative_humidity = sum(
            weather['relativehumidity_2m']) / len(weather['relativehumidity_2m'])
        self.dew_point = sum(
            weather['dewpoint_2m']) / len(weather['dewpoint_2m'])

    def __str__(self):
        return str(self.date)


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
