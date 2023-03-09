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

    def getTrialMonthStats(self,
                           keyName='trial_status__name',
                           title='trials per Status',
                           orientation='v',
                           product=None):
        lastMonth = BaaSHelpers.lastXMonthDateIso(StatsDataApi.LAST_MONTHS)
        filterCriteria = {'created__gt': lastMonth}
        if product:
            filterCriteria['product'] = product
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
        graph = GraphStat(title, datasets, labels,
                          orientation=orientation,
                          xAxis='month', yAxis='# trials')
        return graph.plot()

    def getTrialTotalStats(self,
                           keyName='trial_status__name',
                           title='trials per Status',
                           orientation='h'):
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
        graph = GraphStat(title, {keyName: dataset}, labels,
                          orientation=orientation,
                          showLegend=False,
                          xAxis='month', yAxis='# trials')
        return graph.plot()

    def get(self, request, *args, **kwargs):
        totalTrials = FieldTrial.objects.count()
        stats = [
            {'title': '({}) Totals trials'
                      ' date'.format(totalTrials),
             'graphs': [self.getTrialTotalStats(),
                        self.getTrialTotalStats(keyName='product__name',
                                                title='trials per Product'),
                        self.getTrialTotalStats(keyName='crop__name',
                                                title='trials per Crop')]},
            {'title': 'Last {} months trials distributions by created month'
                      ' date'.format(StatsDataApi.LAST_MONTHS),
             'graphs': [self.getTrialMonthStats(),
                        self.getTrialMonthStats(keyName='product__name',
                                                title='trials per Product'),
                        self.getTrialMonthStats(keyName='crop__name',
                                                title='trials per Crop')]}
        ]
        data = {'stats': stats}
        return render(request, StatsDataApi.TEMPLATE, data)
