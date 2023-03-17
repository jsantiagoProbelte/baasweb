from django.shortcuts import render
from rest_framework.views import APIView
from trialapp.models import Thesis, TreatmentThesis


class ThesisPanelApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
    TEMPLATE = 'panel/quality_panel.html'

    def findThesis(self):
        data = {}
        foundTreatments = 0
        foundTrials = 0
        for thesis in Thesis.objects.all().order_by('field_trial_id'):
            treatments = TreatmentThesis.objects.filter(thesis=thesis)
            if treatments:
                continue
            foundTreatments += 1
            nameTrial = thesis.field_trial.name
            if nameTrial not in data:
                data[nameTrial] = {'id': thesis.field_trial.id, 'thesis':[]}
                foundTrials += 1
            data[nameTrial]['thesis'].append(
                {'id': thesis.id, 'name': thesis.name})
        return {'data': [{'name': name,
                          'id': data[name]['id'],
                          'thesis': data[name]['thesis']}
                         for name in data],
                'foundTrials': foundTrials,
                'foundTreatments': foundTreatments}

    def get(self, request, *args, **kwargs):

        data = self.findThesis()
        return render(request, ThesisPanelApi.TEMPLATE, data)
