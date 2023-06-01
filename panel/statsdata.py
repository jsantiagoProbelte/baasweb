from django.db.models import Count
from django.shortcuts import render
from rest_framework.views import APIView
from trialapp.models import FieldTrial
from baaswebapp.baas_helpers import BaaSHelpers
from baaswebapp.graphs import GraphStat


class StatsDataApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
    TEMPLATE = 'panel/statsdata.html'
    LAST_MONTHS = 6

    def getDatapointStats(self):
        pass

    def getTrialMonthStats(self, dimension):
        keyName = '{}__name'.format(dimension)
        yAxis = 'last {} months created trials'.format(
            StatsDataApi.LAST_MONTHS)
        lastMonth = BaaSHelpers.lastXMonthDateIso(StatsDataApi.LAST_MONTHS)
        filterCriteria = {'created__gt': lastMonth}
        query = FieldTrial.objects.values('created__month', keyName)\
            .annotate(Count('id'))\
            .filter(**filterCriteria)\
            .order_by(keyName, 'created__month')
        datasets = {}
        labels = BaaSHelpers.getLastMonthsInOrder(StatsDataApi.LAST_MONTHS)
        # Sorting in array of values per keyName,month
        for item in query:
            month = BaaSHelpers.monthNameFromInt(item['created__month'])
            datasetKey = item[keyName]
            datasetKey = 'Unknown' if datasetKey is None else datasetKey
            if datasetKey not in datasets:
                datasets[datasetKey] = {label: 0 for label in labels}
            if month in labels:
                datasets[datasetKey][month] += item['id__count']
        # prepare data to display
        return GraphStat(datasets, labels, orientation='v',
                         xAxis='month', yAxis=yAxis, barmode="stack").plot()

    def getTrialTotalStats(self, dimension):
        keyName = '{}__name'.format(dimension)
        query = FieldTrial.objects.values(keyName)\
            .annotate(Count('id')).all()\
            .order_by(keyName)

        dataset = {}
        # Sorting in array of values per keyName
        labels = []
        for item in query:
            datasetKey = item[keyName]
            datasetKey = 'Unknown' if datasetKey is None else datasetKey
            dataset[datasetKey] = item['id__count']
            labels.append(datasetKey)

        # prepare data to display
        return GraphStat({keyName: dataset}, labels,
                         orientation='h',
                         showLegend=False, showTitle=False,
                         xAxis=dimension, yAxis='total trials').plot()

    def generateDataDimension(self, dimension):
        return {'title': 'Product trial distribution',
                'total': self.getTrialTotalStats(dimension),
                'time': self.getTrialMonthStats(dimension)}

    def get(self, request, *args, **kwargs):
        totalTrials = FieldTrial.objects.count()

        stats = [[self.generateDataDimension('trial_status'),
                  self.generateDataDimension('product')],
                 [self.generateDataDimension('crop'),
                  self.generateDataDimension('plague')]]

        data = {'stats': stats, 'totalTrials': totalTrials}
        return render(request, StatsDataApi.TEMPLATE, data)
