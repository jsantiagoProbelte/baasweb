from trialapp.models import Thesis, Replica, Sample, FieldTrial
from trialapp.data_models import DataModel, ThesisData,\
    ReplicaData, Assessment, SampleData
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from baaswebapp.graphs import GraphTrial


class SetDataAssessment(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    # see generateDataPointId
    def post(self, request, format=None):
        # noqa:                     4       3                 2              1
        # noqa: E501 data_point_id-[level]-[assessment_id]-[reference_id]-[fakeId]
        theIds = request.POST['data_point_id'].split('-')
        level = theIds[-4]
        assessment = get_object_or_404(Assessment, pk=theIds[-3])
        value = request.POST['data-point']
        refereceId = theIds[-2]
        # try to find if exists:
        if level == GraphTrial.L_THESIS:
            item = get_object_or_404(Thesis, pk=refereceId)
            ThesisData.setDataPoint(item, assessment, value)
        elif level == GraphTrial.L_REPLICA:
            item = get_object_or_404(Replica, pk=refereceId)
            ReplicaData.setDataPoint(item, assessment, value)
        elif level == GraphTrial.L_SAMPLE:
            sampleNumber = theIds[-1]
            item = Sample.findOrCreate(replica_id=refereceId,
                                       number=sampleNumber)
            SampleData.setDataPoint(item, assessment, value)
        else:
            return Response({'success': False}, status='500')
        return Response({'success': True})


class TrialDataApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']
    _trial = None
    _assessments = None

    def prepareHeader(self):
        headerDates = ['', 'Date']
        headerRatingType = ['', 'Rating Type']
        headerRatingUnit = ['', 'Rating Unit']
        headerRatingPart = ['', 'Part Rated']
        headerBBCH = ['', 'BBCH']
        headerInterval = ['', 'Name/Interval']
        for ass in self._assessments:
            headerDates.append(ass.assessment_date.strftime("%d/%m/%y"))
            headerRatingType.append(ass.rate_type.name)
            headerRatingUnit.append(ass.rate_type.unit)
            partRated = '' if ass.part_rated == 'Undefined' else ass.part_rated
            headerRatingPart.append(partRated)
            headerBBCH.append(ass.crop_stage_majority)
            headerInterval.append(ass.name)

        return [headerDates, headerRatingType, headerRatingUnit,
                headerRatingPart, headerBBCH, headerInterval]

    def preparaRows(self):
        replicas = Replica.getFieldTrialObjects(self._trial)
        lastThesisId = None
        rows = []
        thesisName = ''
        for replica in replicas:
            if replica.thesis_id != lastThesisId:
                thesisName = replica.thesis.name
                lastThesisId = replica.thesis_id
            else:
                thesisName = ''

            values = []
            plotPoints = ReplicaData.objects.filter(reference=replica)
            dataPoints = {point.assessment.id: point.value
                          for point in plotPoints}

            for ass in self._assessments:
                value = dataPoints.get(ass.id, '')
                values.append({
                    'value': value,
                    'item_id': DataModel.generateDataPointId(
                         GraphTrial.L_REPLICA, ass, replica)})
            rows.append(
                {'thesis': thesisName,
                 'replica': replica.name,
                 'color': replica.thesis.number,
                 'values': values})
        return rows

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/trial_data.html'
        trial_id = kwargs.get('pk', None)
        self._trial = get_object_or_404(FieldTrial, pk=trial_id)
        self._assessments = Assessment.getObjects(self._trial)
        header = self.prepareHeader()
        showData = {'header': header, 'dataRows': self.preparaRows(),
                    'fieldTrial': self._trial}
        return render(request, template_name, showData)


# Show Data methods
class DataHelper:
    def __init__(self, assessmentId):
        self._assessment = get_object_or_404(Assessment, pk=assessmentId)
        self._fieldTrial = self._assessment.field_trial
        self._replicas = Replica.getFieldTrialObjects(self._fieldTrial)
        self._thesisTrial = Thesis.getObjects(self._fieldTrial)

    def prepareHeader(self, references):
        header = []
        lastIndex = "Bla"
        colspans = {}
        for reference in references:
            thisIndex = reference.getReferenceIndexDataInput()
            if thisIndex not in colspans:
                colspans[thisIndex] = 0
            colspans[thisIndex] += 1
            if lastIndex == thisIndex:
                thisIndex = ''
            else:
                lastIndex = thisIndex
            header.append({
                'index': thisIndex,
                'color': reference.getBackgroundColor(),
                'name': reference.getKey(),
                'id': reference.id})
        newHeader = []
        for item in header:
            thisIndex = item['index']
            if thisIndex != '':
                item['colspan'] = colspans[thisIndex]
            newHeader.append(item)
        return newHeader

    CLSDATAS = {
        GraphTrial.L_REPLICA: ReplicaData,
        GraphTrial.L_THESIS: ThesisData,
        GraphTrial.L_SAMPLE: SampleData}

    def prepareDataPoints(self, references, level, assSet):
        clsData = DataHelper.CLSDATAS[level]
        dataPoints = clsData.getDataPointsAssessment(self._assessment)
        dataPointsToDisplay = []
        dataPointsForGraph = []
        for reference in references:
            value = ''
            for dataPoint in dataPoints:
                if dataPoint.reference.id == reference.id:
                    value = dataPoint.value
                    dataPointsForGraph.append(dataPoint)
                    break
            dataPointsToDisplay.append({
                'value': value,
                'item_id': DataModel.generateDataPointId(
                    level, self._assessment, reference)})
        rows = [{
            'index': self._assessment.assessment_date,
            'dataPoints': dataPointsToDisplay}]
        return rows, dataPointsForGraph

    def prepareSampleDataPoints(self, replicas, level, assSet):
        fakeSampleIds = range(1, self._fieldTrial.samples_per_replica+1)
        dataPointsForGraph = []
        rows = []
        for fakeSampleId in fakeSampleIds:
            dataPointsToDisplay = []
            for replica in replicas:
                dataPoints = SampleData.getDataPointsPerSampleNumber(
                    self._assessment, fakeSampleId)
                value = ''
                for dataPoint in dataPoints:
                    if dataPoint.reference.replica.id == replica.id:
                        value = dataPoint.value
                        dataPointsForGraph.append(dataPoint)
                        break
                dataPointsToDisplay.append({
                    'value': value,
                    'item_id': DataModel.generateDataPointId(
                        level, self._assessment,
                        replica, fakeSampleId)})
            rows.append({
                'index': fakeSampleId,
                'dataPoints': dataPointsToDisplay})
        return rows, dataPointsForGraph

    def prepareAssSet(self, level, assSet,
                      references):
        graph = 'Add data and refresh to show graph'
        if level == GraphTrial.L_SAMPLE:
            rows, pointForGraph = self.prepareSampleDataPoints(
                references, level, assSet)
        else:
            rows, pointForGraph = self.prepareDataPoints(
                references, level, assSet)
        # Calculate graph
        pointsInGraphs = len(pointForGraph)
        if pointsInGraphs > 1:
            graphHelper = GraphTrial(
                level, assSet,
                self._assessment.part_rated, pointForGraph)
            graph = graphHelper.draw()
        return rows, graph, pointsInGraphs

    TOKEN_LEVEL = {
        GraphTrial.L_REPLICA: 'dataPointsR',
        GraphTrial.L_THESIS: 'dataPointsT',
        GraphTrial.L_SAMPLE: 'dataPointsS'}

    def showDataPerLevel(self, level, onlyThisData=False):
        references = None
        subtitle = 'Assessment'
        if level == GraphTrial.L_THESIS:
            references = self._thesisTrial
        elif level == GraphTrial.L_REPLICA:
            references = self._replicas

        elif level == GraphTrial.L_SAMPLE:
            references = self._replicas
            subtitle = 'Samples'
            if not self._fieldTrial.samples_per_replica:
                return {DataHelper.TOKEN_LEVEL[level]: [{
                    'errors': 'Number of samples per replica '
                              'is not defined. Go to field trial'
                              'definition'}]}, 0
        totalPoints = 0
        header = self.prepareHeader(references)
        rows, graph, pointsInGraph = self.prepareAssSet(
            level, self._assessment.rate_type, references)
        dataPointsList = [{
            'title': self._assessment.rate_type.getName(),
            'subtitle': subtitle,
            'header': header, 'errors': '',
            'graph': graph, 'rows': rows}]
        totalPoints += pointsInGraph
        return self.returnData(
            {DataHelper.TOKEN_LEVEL[level]: dataPointsList},
            onlyThisData), totalPoints

    def returnData(self, dataToReturned, onlyThisData):
        if onlyThisData:
            return dataToReturned
        else:
            common = {
                'title': self._assessment.getTitle(),
                'assessment': self._assessment,
                'theses': self._thesisTrial,
                'fieldTrial': self._fieldTrial}
            return {**common, **dataToReturned}

    def makeActiveView(self, pointsR, pointsT):
        active = GraphTrial.L_SAMPLE
        if pointsR > 0:
            active = GraphTrial.L_REPLICA
        elif pointsT > 0:
            active = GraphTrial.L_THESIS
        activeViews = {}
        for level in GraphTrial.LEVELS:
            navActive = ''
            tabActive = ''
            if level == active:
                navActive = 'active'
                tabActive = 'show active'
            activeViews['{}_nav'.format(level)] = navActive
            activeViews['{}_tab'.format(level)] = tabActive
        return activeViews

    def showDataAssessment(self):
        dataR, pR = self.showDataPerLevel(GraphTrial.L_REPLICA)
        dataT, pT = self.showDataPerLevel(GraphTrial.L_THESIS,
                                          onlyThisData=True)
        dataS, pS = self.showDataPerLevel(GraphTrial.L_SAMPLE,
                                          onlyThisData=True)
        activeViews = self.makeActiveView(pR, pT)
        return {**dataR, **dataT, **dataS, **activeViews}
