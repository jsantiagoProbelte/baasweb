# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
import panel.weatherhelper as weatherhelper
import panel.riskcalc as riskcalc
from baaswebapp.baas_helpers import BaaSHelpers
from baaswebapp.graphs import WeatherGraphFactory


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
            graphs = WeatherGraphFactory.build(
                weather[weatherhelper.DATES], weather[weatherhelper.DATES],
                weather[weatherhelper.WT_TAG_TEMPS], None,  # min_temps,
                None, None, weather[weatherhelper.WT_PREC_HOURS], None,
                None, None, None,
                None, None, None,
                # max_temps, precip, precip_hrs, soil_moist_1,
                # soil_moist_2, soil_moist_3, soil_moist_4,
                # soil_temps_1, soil_temps_2, soil_temps_3,
                # soil_temps_4, rel_humid, dew_point)
                None, weather[weatherhelper.WT_HUMIDITY],
                weather[weatherhelper.WT_DEW_TEMP])

            daily_weather = weatherhelper.formatDaily(weather)
            risks = riskcalc.computeRisks(weather)
            days = BaaSHelpers.nextXDays(RecomenderApi.NEXT_DAYS)
            return {'days': days,
                    'daily_weather': self.convertToArray(daily_weather),
                    'risks': self.convertToArray(risks),
                    'weatherGraph': graphs}
        else:
            return {}

    def get(self, request, *args, **kwargs):
        data = self.fetchData(request)
        return render(request, RecomenderApi.TEMPLATE, data)

    def convertToArray(self, dictionary):
        theArray = []
        for key in dictionary:
            values = dictionary[key]
            values.insert(0, key)
            theArray.append(values)
        return theArray
