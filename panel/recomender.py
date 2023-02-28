# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView


class RecomenderApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get', 'post']
    DEFAULT_LATITUDE = 38.034670
    DEFAULT_LONGITUDE = -1.189287
    TEMPLATE = 'panel/recomender.html'

    def fetchWeather(self, latitude, longitude):
        return {
            'Forecast': ['Day1', 'Day2', 'Day3', 'Day4', 'Day5'],
            'Temperature (C)': [15, 17, 18, 15, 20],
            'Humidity (%)': [80, 90, 85, 80, 100]}

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
        weather = self.fetchWeather(latitude, longitude)
        return {'latitude': latitude,
                'longitude': longitude,
                'weather': weather,
                'risk': self.computeRisks(weather)}

    def get(self, request, *args, **kwargs):
        data = self.prepareData(kwargs)
        return render(request, RecomenderApi.TEMPLATE, data)

    def post(self, request, *args, **kwargs):
        data = self.prepareData(kwargs)
        return render(request, RecomenderApi.TEMPLATE, data)
