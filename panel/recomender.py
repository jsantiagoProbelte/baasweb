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
            str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')) + '--'
            + str((datetime.now() + timedelta(days=4)).strftime('%Y-%m-%dT%H:%M:%SZ')) +
            ':P1D/t_min_2m_1h:C,dew_point_2m:C,absolute_humidity_2m:gm3/' +
            str(latitude) + ','
            + str(longitude) + '/json?model=mix', headers=headers)
        res_json = json.loads(res.content)
        return res_json

    def getLatLong(self, kwargs):
        latitude = RecomenderApi.DEFAULT_LATITUDE
        longitude = RecomenderApi.DEFAULT_LONGITUDE
        if 'latitude' in kwargs:
            latitude = kwargs['latitude']
        if 'longitude' in kwargs:
            longitude = kwargs['longitude']
        return latitude, longitude

    def computeRisks(self, weather):
        return {
            'Risks': ['Day1', 'Day2', 'Day3', 'Day4', 'Day5'],
            'Botrytis': ['High', 'Low', 'Medium', 'Low', 'High'],
            'Procesionary': ['Low', 'Low', 'High', 'Low', 'Low'],
        }

    def prepareData(self, kwargs):
        latitude, longitude = self.getLatLong(kwargs)
        weather = self.fetchTestWeather(latitude, longitude)
        return {'latitude': latitude,
                'longitude': longitude,
                'weather': weather,
                'risk': self.computeRisks(weather)}

    def get(self, request, *args, **kwargs):
        data = self.prepareData(kwargs)
        return render(request, RecomenderApi.TEMPLATE, data)

    def post(self, request, *args, **kwargs):
        latitude = request.POST["latitude"]
        longitude = request.POST["longitude"]
        weather = self.fetchWeather(latitude, longitude)
        risks = self.computeRisks(weather)
        return JsonResponse(weather)
