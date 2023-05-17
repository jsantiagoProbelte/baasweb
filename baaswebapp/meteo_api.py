from django.shortcuts import redirect
from rest_framework.views import APIView
from trialapp.data_models import Assessment
from trialapp.models import FieldTrial
from catalogue.models import Weather
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta


class MeteoApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def enrich_assessment(self, assessment, field_trial):
        existing = Weather.objects.filter(date=assessment.assessment_date,
                                          longitude=field_trial.longitude,
                                          latitude=field_trial.latitude).first()
        if existing:
            if existing.recent and existing.date < (datetime.now() - timedelta(days=7)).date():
                existing.fetchWeather()
                existing.save()
            return
        weather = Weather(date=assessment.assessment_date,
                          longitude=field_trial.longitude, latitude=field_trial.latitude)
        weather.fetchWeather()
        weather.save()
        return

    def get(self, request, *args, **kwargs):
        field_trial_id = kwargs.get('field_trial_id', None)
        field_trial = get_object_or_404(FieldTrial, pk=field_trial_id)
        assessments = Assessment.getObjects(field_trial_id)
        for assessment in assessments:
            self.enrich_assessment(assessment, field_trial)
        return redirect('/assessment_list/' + str(field_trial_id) + '/')
