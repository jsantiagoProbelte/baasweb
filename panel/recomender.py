# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
import requests
import json
from datetime import timedelta, datetime
from django.http import JsonResponse
import base64

# Secret
base64key = base64.b64encode(
    "probelte_arentz:z0GuO6Tk6l".encode("ascii")).decode("ascii")


class RecomenderApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get', 'post']
    DEFAULT_LATITUDE = 38.034670
    DEFAULT_LONGITUDE = -1.189287
    TEMPLATE = 'panel/recomender.html'

    def fetchTestWeather(self, latitude, longitude):
        return {
            'Forecast': ['Day1', 'Day2', 'Day3', 'Day4', 'Day5'],
            'Temperature (C)': [15, 17, 18, 15, 20],
            'Humidity (%)': [80, 90, 85, 80, 100]}

    def fetchWeather(self, latitude, longitude):
        headers = {'Authorization': 'Basic ' + base64key}
        res = requests.get(
            'https://api.meteomatics.com/' +
            datetime.now().strftime('%Y-%m-%dT00:00:00Z') +
            'P5D:PT1H/t_min_2m_1h:C,dew_point_2m:C,absolute_humidity_2m:gm3/' +
            str(latitude) + ','
            + str(longitude) + '/json?model=mix', headers=headers)
        res_json = json.loads(res.content)

        return self.formatWeather(res_json)

    def getLatLong(self, kwargs):
        latitude = RecomenderApi.DEFAULT_LATITUDE
        longitude = RecomenderApi.DEFAULT_LONGITUDE
        if 'latitude' in kwargs:
            latitude = kwargs['latitude']
        if 'longitude' in kwargs:
            longitude = kwargs['longitude']
        return latitude, longitude

    def computeRisks(self, weather):
        c = 0.5
        count = len(weather['temperatures'])
        temperatures = weather['temperatures']
        dew_temperatures = weather['dew_temperatures']
        lwd = []
        botrytis_risks = []
        for i in range(count):
            lwd.append((temperatures[i]['value'] -
                       dew_temperatures[i]['value']) * c)

        for i in range(count):
            temp = temperatures[i]['value']
            risk = -4.268 - 0.0901 * lwd[i] + 0.294 * lwd[i] * temp - \
                2.35 * 10 - 5 * lwd[i] * (temp ** 3)
            botrytis_risks.append(risk)

        return {
            'botrytis': botrytis_risks
        }
        """
        return {
            'Risks': ['Day1', 'Day2', 'Day3', 'Day4', 'Day5'],
            'Botrytis': ['High', 'Low', 'Medium', 'Low', 'High'],
            'Procesionary': ['Low', 'Low', 'High', 'Low', 'Low'],
        }
        """

    def prepareData(self, kwargs):
        latitude, longitude = self.getLatLong(kwargs)
        # weather = self.fetchTestWeather(latitude, longitude)
        return {'latitude': latitude,
                'longitude': longitude}

    def formatWeather(self, res_json):
        temperatures = res_json['data'][0]['coordinates'][0]['dates']
        dew_temperatures = res_json['data'][1]['coordinates'][0]['dates']
        humidities = res_json['data'][2]['coordinates'][0]['dates']

        # Meteomatics always returns 1 hour extra, so we pop it.
        temperatures.pop()
        dew_temperatures.pop()
        humidities.pop()

        return {
            'temperatures': temperatures,
            'dew_temperatures': dew_temperatures,
            'humidities': humidities
        }

    def formatDaily(self, weather):
        offset = 12
        temperatures = weather['temperatures']
        dew_temperatures = weather['dew_temperatures']
        humidities = weather['humidities']

        daily_temperatures = []
        daily_dew = []
        daily_humidity = []

        for i in range(len(temperatures)):
            if i % 24 == 0:
                daily_temperatures.append(temperatures[i + offset])
                daily_dew.append(dew_temperatures[i + offset])
                daily_humidity.append(humidities[i + offset])
                print(temperatures[i + offset]['date'])

        return {
            'temperatures': daily_temperatures,
            'dew_temperatures': daily_dew,
            'humidities': daily_humidity
        }

    def formatHourly(self, weather):
        return

    def get(self, request, *args, **kwargs):
        data = self.prepareData(kwargs)
        return render(request, RecomenderApi.TEMPLATE, data)

    def post(self, request, *args, **kwargs):
        latitude = request.POST["latitude"]
        longitude = request.POST["longitude"]
        weather = self.fetchWeather(latitude, longitude)
        daily_weather = self.formatDaily(weather)
        risks = self.computeRisks(daily_weather)

        return JsonResponse({'daily_weather': daily_weather, 'risks': risks}, safe=False)
