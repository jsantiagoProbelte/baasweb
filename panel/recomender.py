# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
import panel.weatherhelper as weatherhelper
import panel.riskcalc as riskcalc
from baaswebapp.baas_helpers import BaaSHelpers


class RecomenderApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
    DEFAULT_LATITUDE = 38.034670
    DEFAULT_LONGITUDE = -1.189287
    TEMPLATE = 'panel/recomender.html'
    NEXT_DAYS = 5

    def fetchData(self, request):
        latitude = request.GET.get("latitude",
                                   RecomenderApi.DEFAULT_LATITUDE)
        longitude = request.GET.get("longitude",
                                    RecomenderApi.DEFAULT_LONGITUDE)
        if longitude and latitude:
            weather = weatherhelper.fetchOpenWeather(
                latitude, longitude, RecomenderApi.NEXT_DAYS)
            daily_weather = weatherhelper.formatDaily(weather)
            risks = riskcalc.computeRisks(weather)
            days = BaaSHelpers.nextXDays(RecomenderApi.NEXT_DAYS)
            return {'days': days,
                    'daily_weather': self.convertToArray(daily_weather),
                    'risks': self.convertToArray(risks, isDict=False)}
        else:
            return {}

    def get(self, request, *args, **kwargs):
        data = self.fetchData(request)
        return render(request, RecomenderApi.TEMPLATE, data)

    def convertToArray(self, dictionary, isDict=True):
        theArray = []
        for key in dictionary:
            values = dictionary[key]
            row = []
            if isDict:
                for item in values:
                    row.append(item['value'])
            else:
                row = values
            row.insert(0, key)
            theArray.append(row)
        return theArray
