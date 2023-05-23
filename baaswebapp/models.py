from django.db import models
from datetime import datetime, timedelta
import urllib.parse
import requests


class ModelHelpers:
    NULL_STRING = '------'
    UNKNOWN = ' Unknown'
    UNDEFINED = 'Undefined'

    @classmethod
    def getUnknown(cls):
        return cls.objects.get(name=ModelHelpers.UNKNOWN)

    def isUnknown(self):
        return self.name == ModelHelpers.UNKNOWN

    @classmethod
    def getObjects(cls):
        return cls.objects.all().order_by('name')

    @classmethod
    def findOrCreate(cls, **args):
        objs = cls.objects.filter(**args)
        if objs:
            return objs[0]
        else:
            return cls.objects.create(**args)

    @classmethod
    def returnFormatedItem(cls, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        return cls._getSelectList(cls.getObjects().order_by('name'),
                                  addNull=addNull,
                                  asDict=asDict)

    @classmethod
    def _getSelectList(cls, items, addNull=False, asDict=False):
        theList = []
        for item in items:
            theList.append(cls.returnFormatedItem(
                asDict, item.id, item.getName()))

        if addNull:
            theList.insert(
                0,
                cls.returnFormatedItem(
                    asDict,
                    None,
                    ModelHelpers.NULL_STRING))

        return theList

    def getKey(self):
        return self.getName()

    def getName(self):
        return self.name

    def __str__(self):
        return self.getName()

    @classmethod
    def extractDistincValues(cls, results, tag_id, tag_name):
        values = {}
        for result in results:
            found = result[tag_id]
            name = result[tag_name]
            if name in [ModelHelpers.UNKNOWN, 'N/A']:
                continue
            if found not in values:
                values[found] = name
        dimensionsDic = [{'value': id, 'name': values[id]} for id in values]
        return dimensionsDic, list(values.keys())


class RateTypeUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True)

    def getName(self):
        return '{} ({})'.format(self.name, self.unit)

    def __str__(self):
        return self.getName()


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
        url = ('https://archive-api.open-meteo.com/v1/archive?daily=' +
               'temperature_2m_max,temperature_2m_min,precipitation_sum,' +
               'precipitation_hours,windspeed_10m_max&timezone=auto&')
        if self.date > (datetime.now() - timedelta(days=7)).date():
            url = ('https://api.open-meteo.com/v1/forecast?daily=' +
                   'temperature_2m_max,temperature_2m_min,precipitation_sum,' +
                   'precipitation_hours,windspeed_10m_max&timezone=auto&')
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
        url = ('https://archive-api.open-meteo.com/v1/archive?hourly=' +
               'soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,' +
               'soil_temperature_28_to_100cm,soil_temperature_100_to_255cm,' +
               'soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,' +
               'soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,' +
               'relativehumidity_2m,dewpoint_2m&timezone=auto&')
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
        self.soil_temp_0_to_7cm = (sum(
            weather['soil_temperature_0_to_7cm']) /
            len(weather['soil_temperature_0_to_7cm']))
        self.soil_temp_7_to_28cm = (sum(
            weather['soil_temperature_7_to_28cm']) /
            len(weather['soil_temperature_7_to_28cm']))
        self.soil_temp_28_to_100cm = (sum(
            weather['soil_temperature_28_to_100cm']) /
            len(weather['soil_temperature_28_to_100cm']))
        self.soil_temp_100_to_255cm = (sum(
            weather['soil_temperature_100_to_255cm']) /
            len(weather['soil_temperature_100_to_255cm']))

        self.soil_moist_0_to_7cm = (sum(
            weather['soil_moisture_0_to_7cm']) /
            len(weather['soil_moisture_0_to_7cm']))
        self.soil_moist_7_to_28cm = (sum(
            weather['soil_moisture_7_to_28cm']) /
            len(weather['soil_moisture_7_to_28cm']))
        self.soil_moist_28_to_100cm = (sum(
            weather['soil_moisture_28_to_100cm']) /
            len(weather['soil_moisture_28_to_100cm']))
        self.soil_moist_100_to_255cm = (sum(
            weather['soil_moisture_100_to_255cm']) /
            len(weather['soil_moisture_100_to_255cm']))
        self.relative_humidity = (sum(
            weather['relativehumidity_2m']) /
            len(weather['relativehumidity_2m']))
        self.dew_point = sum(
            weather['dewpoint_2m']) / len(weather['dewpoint_2m'])

    def __str__(self):
        return str(self.date)
