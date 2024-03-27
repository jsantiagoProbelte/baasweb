from django.db import models
from datetime import datetime, timedelta
import urllib.parse
import requests
from django.utils.translation import gettext_lazy as _


class PType(models.TextChoices):
    UNKNOWN = 'UNK', _('Unknown')
    FERTILIZER = 'FRT', _('Fertilizer')
    ESTIMULANT = 'EST', _('Estimulant')
    INSECTICIDE = 'INS', _('Insecticide')
    NEMATICIDE = 'NMC', _('Nematicide')
    FUNGICIDE = 'FGC', _('Fungicide')
    HERBICIDE = 'HRB', _('Herbicide')


class Category(models.TextChoices):
    NUTRITIONAL = 'NUT', _('Nutritional')
    ESTIMULANT = 'EST', _('Estimulant')
    CONTROL = 'CTL', _('Control')
    UNKNOWN = 'UNK', _('Unknown')


class ModelHelpers:
    NULL_STRING = '------'
    UNKNOWN = ' Unknown'
    UNDEFINED = 'Undefined'
    NOT_APPLICABLE = 'N/A'
    THE_UNKNNOWNS = [UNKNOWN, NULL_STRING, NOT_APPLICABLE, UNDEFINED]

    @classmethod
    def isInUnknowns(self, str):
        if str in ModelHelpers.THE_UNKNNOWNS:
            return True
        return False

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


class RateTypeUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True)
    display_order = models.IntegerField(blank=True, null=True, default=0)

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

    @classmethod
    def needEnrich(cls, firstDate, lastDate, latitude, longitude):
        count = cls.objects.filter(date__range=(firstDate, lastDate),
                                   longitude=longitude,
                                   latitude=latitude).count()
        days = (lastDate-firstDate).days
        if count < days:
            return True
        else:
            return False

    @classmethod
    def enrich(cls, firstDate, lastDate, latitude, longitude):
        if firstDate and lastDate and latitude and longitude:
            if cls.needEnrich(firstDate, lastDate, latitude, longitude):
                one_day = timedelta(days=1)
                thisDay = firstDate
                while thisDay != lastDate:
                    isWeather = cls.objects.filter(
                        date=thisDay, longitude=longitude,
                        latitude=latitude).exists()
                    if not isWeather:
                        weather = Weather(
                            date=thisDay,
                            longitude=longitude,
                            latitude=latitude)
                        weather.fetchWeather()
                        weather.save()
                    thisDay += one_day

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


class EventBaas(models.TextChoices):
    UNKNOWN = 'UNK', 'Unknown'
    NEW_TRIAL = 'N_T', 'new trial'
    UPDATE_TRIAL = 'U_T', 'update trial'
    DELETE_TRIAL = 'D_T', 'delete trial'
    TRIAL_DONE = 'T_D', 'trial done'
    NEW_THESIS = 'N_TH', 'new thesis'
    UPDATE_THESIS = 'U_TH', 'update thesis'
    DELETE_THESIS = 'D_TH', 'delete thesis'
    NEW_ASS = 'N_ASS', 'new assessment'
    UPDATE_ASS = 'U_ASS', 'update assessment'
    DELETE_ASS = 'D_ASS', 'delete assessment'
    NEW_APP = 'N_APP', 'new application'
    UPDATE_APP = 'U_APP', 'update application'
    DELETE_APP = 'D_APP', 'delete application'
    NEW_PRODUCT = 'N_P', 'new product'
    UPDATE_PRODUCT = 'U_P', 'update product'
    DELETE_PRODUCT = 'D_P', 'delete product'
    NEW_TREATMENT = 'N_TT', 'new TREATMENT'
    UPDATE_TREATMENT = 'U_TT', 'update TREATMENT'
    DELETE_TREATMENT = 'D_TT', 'delete TREATMENT'
    NEW_DATA = 'N_DT', 'new data'

    @classmethod
    def get_label(cls, value):
        for choice in cls.choices:
            if choice[0] == value:
                return choice[1]
        return None


class EventLog(ModelHelpers, models.Model):
    event = models.CharField(
        max_length=10,
        choices=EventBaas.choices,
        default=EventBaas.UNKNOWN)
    timestamp = models.DateTimeField(auto_now_add=True)
    user_id = models.IntegerField()
    obj_id = models.IntegerField(null=True)

    @classmethod
    def track(cls, name, user_id, obj_id=None):
        EventLog.objects.create(
            event=name, user_id=user_id,
            obj_id=obj_id)
