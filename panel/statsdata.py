from django.db.models import Count
from django.shortcuts import render
from rest_framework.views import APIView
from trialapp.models import FieldTrial
from baaswebapp.baas_helpers import BaaSHelpers
from baaswebapp.graphs import GraphStat, PieGraph
from baaswebapp.models import EventLog, EventBaas
from django.db.models.functions import TruncWeek


class StatsDataApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
    TEMPLATE = 'panel/statsdata.html'
    LAST_MONTHS = 6

    def getDatapointStats(self):
        pass

    def getFilterFromDimension(self, dimension):
        if dimension == 'status_trial':
            return dimension
        else:
            return '{}__name'.format(dimension)

    def getTrialMonthStats(self, dimension, topList):
        keyName = self.getFilterFromDimension(dimension)
        yAxis = 'last {} months created trials'.format(
            StatsDataApi.LAST_MONTHS)
        lastMonth = BaaSHelpers.lastXMonthDateIso(StatsDataApi.LAST_MONTHS)
        filterCriteria = {'created__gt': lastMonth}
        query = FieldTrial.objects.values('created__month', keyName)\
            .annotate(Count('id'))\
            .filter(**filterCriteria)\
            .order_by(keyName, 'created__month')
        datasets = {}
        months = BaaSHelpers.getLastMonthsInOrder(StatsDataApi.LAST_MONTHS)
        # Sorting in array of values per keyName,month
        topList.append('Other')
        datasets = {datasetKey: {label: 0 for label in months}
                    for datasetKey in topList}
        for item in query:
            month = BaaSHelpers.monthNameFromInt(item['created__month'])
            datasetKey = item[keyName]
            if datasetKey is None or datasetKey not in topList:
                datasetKey = 'Other'
            if month in months:
                datasets[datasetKey][month] += item['id__count']

        accValues = {}
        for key in topList:
            lastValue = 0
            accValues[key] = {}
            for month in months:
                thisMonthValue = 0
                if month in datasets[key]:
                    thisMonthValue = datasets[key][month]
                lastValue += thisMonthValue
                accValues[key][month] = lastValue

        # prepare data to display
        return GraphStat(accValues, months, orientation='v', showLegend=False,
                         xAxis='month', yAxis=yAxis, barmode="stack").plot()

    def getTrialTotalStats(self, dimension):
        keyName = self.getFilterFromDimension(dimension)
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
        sizeTops = 6
        for label in newlabels:
            topList.append(label)
            sizeTops -= 1
            if sizeTops == 0:
                break
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

    def generateEventGraphs(self):
        events = EventLog.objects.values('event')\
            .annotate(Count('id')).all()\
            .order_by('id__count')

        dataset = {}
        # Sorting in array of values per keyName
        labels = []
        topList = []
        for item in events:
            datasetKey = EventBaas.get_label(item['event'])
            datasetKey = 'Unknown' if datasetKey is None else datasetKey
            dataset[datasetKey] = item['id__count']
            labels.append(datasetKey)

        # reverse order of labels to draw from top to bottom
        newlabels = list(reversed(labels))
        sizeTops = 25
        for label in newlabels:
            topList.append(label)
            sizeTops -= 1
            if sizeTops == 0:
                break
        # prepare data to display
        return GraphStat({'event': dataset}, newlabels,
                         orientation='h',
                         showLegend=False, showTitle=False,
                         xAxis='events', yAxis='total events').plot()

    def generateEventWeeklyGraphs(self):
        events = EventLog.objects.annotate(
                week=TruncWeek('timestamp')
            ).values(
                'week', 'event'
            ).annotate(
                count=Count('id')
            ).order_by('week', 'event')
        dataset = {}
        weeks = set()
        counts = {}
        for item in events:
            week = item['week'].strftime("%U")
            eventKey = EventBaas.get_label(item['event'])
            weeks.add(week)
            value = item['count']
            if eventKey not in dataset:
                dataset[eventKey] = {}
            if eventKey not in counts:
                counts[eventKey] = 0
            if week not in dataset[eventKey]:
                dataset[eventKey][week] = 0
            thisWeekValue = counts[eventKey] + value
            dataset[eventKey][week] = thisWeekValue
            counts[eventKey] = thisWeekValue

        # fill the gaps, not all week may have values
        weeksList = list(weeks)
        weeksList.sort()
        accValues = {}
        for event in dataset:
            accValues[event] = {}
            lastValue = 0
            for week in weeksList:
                if week in dataset[event]:
                    lastValue = dataset[event][week]
                accValues[event][week] = lastValue

        # prepare data to display
        return GraphStat(accValues, weeksList, orientation='v',
                         showLegend=True,
                         xAxis='week', yAxis='Events', barmode="stack").plot()

    def get(self, request, *args, **kwargs):
        totalTrials = FieldTrial.objects.count()

        stats = [[self.generateDataDimension('status_trial', 'Trial Status'),
                  self.generateDataDimension('product', 'Products')],
                 [self.generateDataDimension('crop', 'Crops'),
                  self.generateDataDimension('plague', 'Pests & Diseases')]]
        publics = FieldTrial.objects.filter(
            public=True, trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL).count()
        favorables = FieldTrial.objects.filter(
            favorable=True, trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL).count()
        publicGraph = PieGraph.draw(publics, 'Public', totalTrials)
        favorGraph = PieGraph.draw(favorables, 'Favorable', totalTrials)
        data = {'stats': stats, 'totalTrials': totalTrials,
                'publicGraph': publicGraph, 'favorGraph': favorGraph,
                'eventsGraph': self.generateEventGraphs(),
                'eventsWeeklyGraph': self.generateEventWeeklyGraphs()}
        return render(request, StatsDataApi.TEMPLATE, data)
