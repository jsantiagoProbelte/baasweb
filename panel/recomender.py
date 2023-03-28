# Create your views here.
from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse

import panel.weatherhelper as weatherhelper
import panel.riskcalc as riskcalc


class RecomenderApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get', 'post']
    DEFAULT_LATITUDE = 38.034670
    DEFAULT_LONGITUDE = -1.189287
    TEMPLATE = 'panel/recomender.html'

    def get(self, request, *args, **kwargs):
        return render(request, RecomenderApi.TEMPLATE)

    def post(self, request, *args, **kwargs):
        latitude = request.POST["latitude"]
        longitude = request.POST["longitude"]

        weather = weatherhelper.fetchOpenWeather(latitude, longitude)
        daily_weather = weatherhelper.formatDaily(weather)
        risks = riskcalc.computeRisks(weather)

        return JsonResponse({'daily_weather': daily_weather, 'risks': risks}, safe=False)
