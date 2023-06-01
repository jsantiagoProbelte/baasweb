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

    def getTrialMonthStats(self, dimension, topList):
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
        topList.append('Other')
        datasets = {datasetKey: {label: 0 for label in labels}
                    for datasetKey in topList}
        for item in query:
            month = BaaSHelpers.monthNameFromInt(item['created__month'])
            datasetKey = item[keyName]
            if datasetKey is None or datasetKey not in topList:
                datasetKey = 'Other'
            if month in labels:
                datasets[datasetKey][month] += item['id__count']
        # prepare data to display
        return GraphStat(datasets, labels, orientation='v', showLegend=False,
                         xAxis='month', yAxis=yAxis, barmode="stack").plot()

    def getTrialTotalStats(self, dimension):
        keyName = '{}__name'.format(dimension)
        query = FieldTrial.objects.values(keyName)\
            .annotate(Count('id')).all()\
            .order_by('id__count')

        dataset = {}
        # Sorting in array of values per keyName
        labels = []
        topList = []
        for item in query:
            datasetKey = item[keyName]
            datasetKey = 'Unknown' if datasetKey is None else datasetKey
            dataset[datasetKey] = item['id__count']
            labels.append(datasetKey)

        # reverse order of labels to draw from top to bottom
        newlabels = list(reversed(labels))
        for index in range(6):
            topList.append(newlabels[index])
        # prepare data to display
        return GraphStat({keyName: dataset}, newlabels,
                         orientation='h',
                         showLegend=False, showTitle=False,
                         xAxis=dimension, yAxis='total trials').plot(), topList

    def generateDataDimension(self, dimension, title):
        totalGraph, topList = self.getTrialTotalStats(dimension)
        return {'title': title,
                'total': totalGraph,
                'time': self.getTrialMonthStats(dimension, topList)}

    def get(self, request, *args, **kwargs):
        totalTrials = FieldTrial.objects.count()

        stats = [[self.generateDataDimension('trial_status', 'Trial Status'),
                  self.generateDataDimension('product', 'Products')],
                 [self.generateDataDimension('crop', 'Crops'),
                  self.generateDataDimension('plague', 'Plagues & Sickness')]]

        data = {'stats': stats, 'totalTrials': totalTrials}
        return render(request, StatsDataApi.TEMPLATE, data)
