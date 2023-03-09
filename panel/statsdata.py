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

    def getFieldtrialStats(self,
                           keyName='trial_status__name',
                           title='Trials per status',
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
                          xAxis='month', yAxis='# trials')
        return graph.plot()

    def get(self, request, *args, **kwargs):
        totalTrials = FieldTrial.objects.count()
        stats = [
            {'title': '({}) Trials'.format(totalTrials),
             'graphs': [self.getFieldtrialStats(),
                        self.getFieldtrialStats(keyName='product__name',
                                                title='Trials per product')]}
        ]
        data = {'stats': stats}
        return render(request, StatsDataApi.TEMPLATE, data)
