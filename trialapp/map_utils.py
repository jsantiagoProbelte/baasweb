import json
from django.http import JsonResponse
from django.views import View
from trialapp.models import FieldTrial
from django.contrib.auth.mixins import LoginRequiredMixin


class MapApiHelper():
    _trialIds = None
    _coordinates = None
    _trials = None

    def __init__(self, trialIds):
        self._trialIds = trialIds
        self.__set_trials()

    def __set_trials(self):
        self._trials = FieldTrial.objects.all().filter(id__in=self._trialIds)

    def get_trials_coordinates(self):
        print(self._trials)
        coordinates = []
        for trial in self._trials:
            print(f"{trial.latitude} - {trial.longitude}")

            if trial.latitude and trial.longitude:
                coordinates.append([trial.longitude, trial.latitude])

        self._coordinates = coordinates
        return self._coordinates


class MapApi(LoginRequiredMixin, View):
    model = FieldTrial

    def post(self, request):
        requestBody = json.loads(request.body)
        print(requestBody)
        helper = MapApiHelper(requestBody)

        coordinates = helper.get_trials_coordinates()
        print(coordinates)
        object = {'coordinates': coordinates}

        return JsonResponse(object, status=200)
