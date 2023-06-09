from baaswebapp.models import RateTypeUnit
from trialapp.models import Thesis, Replica, Sample, FieldTrial,\
    TreatmentThesis
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

    def addValue(self, array, assessment, key, value):
        array.append({'name': key, 'value': value, 'id': assessment.id})

    def prepareHeader(self):
        partRatedArr = []
        bbchArr = []
        names = []
        dates = []
        rating = []
        for ass in self._assessments:
            self.addValue(names, ass, 'name', ass.name)
            self.addValue(dates, ass, 'assessment_date',
                          ass.assessment_date.isoformat())
            self.addValue(rating, ass, 'rate_type', ass.rate_type.id)

            partRated = ass.part_rated
            if partRated == 'Undefined' or partRated == 'None':
                partRated = ''
            self.addValue(partRatedArr, ass, 'part_rated', partRated)
            bbch = ass.crop_stage_majority
            if bbch == 'Undefined' or bbch == 'None':
                bbch = ''
            self.addValue(bbchArr, ass, 'crop_stage_majority', bbch)

        return {
            'ids': [{'id': ass.id, 'name': ass.name}
                    for ass in self._assessments],
            'bbch': bbchArr,
            'partRated': partRatedArr,
            'rating': rating,
            'names': names,
            'dates': dates}

    def preparaRows(self):
        replicas = Replica.getFieldTrialObjects(self._trial)
        lastThesisId = None
        rows = []
        thesisName = ''
        rowspan = self._trial.replicas_per_thesis
        for replica in replicas:
            if replica.thesis_id != lastThesisId:
                thesisName = replica.thesis.name
                lastThesisId = replica.thesis_id
                thisRowspan = rowspan
            else:
                thesisName = ''
                thisRowspan = 0

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
                 'rowspan': thisRowspan,
                 'replica': replica.name,
                 'color': replica.thesis.number,
                 'values': values})
        return rows

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/trial_data.html'
        trial_id = kwargs.get('pk', None)
        self._trial = get_object_or_404(FieldTrial, pk=trial_id)
        self._assessments = Assessment.getObjects(
            self._trial, date_order=False)
        header = self.prepareHeader()
        showData = {'header': header, 'dataRows': self.preparaRows(),
                    'ratings': RateTypeUnit.getSelectList(asDict=True),
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
        dataPoints = clsData.getDataPoints(self._assessment)
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
            graphHelper = DataGraphFactory(
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


class DataGraphFactory():
    _level = None
    _graph = None
    _references = {}
    _colors = {}

    def __init__(self, level, rateType, ratedPart,
                 dataPoints, xAxis=GraphTrial.L_DATE,
                 showTitle=True):
        self._level = level
        self._references = {}
        self._colors = {}
        traces = self.buildData(dataPoints, xAxis)
        if len(traces) > 0:
            self._graph = GraphTrial(level, rateType, ratedPart,
                                     traces, xAxis=xAxis,
                                     showTitle=showTitle)
        else:
            self._graph = 'No data points found'

    def buildData(self, dataPoints, xAxis):
        # This is for diplay purposes. [[,],[,]...]
        # It has to follow the order of references
        # and then trial assessments
        if dataPoints is None or len(dataPoints) == 0:
            return None
        traces = {}
        for dataPoint in dataPoints:
            # TODO: there could be data with different units
            pointRef = self.getPointRefence(dataPoint)
            traceId = self.traceId(pointRef)

            self.assignColor(traceId)
            if traceId not in traces:
                traces[traceId] = self.prepareTrace(pointRef)
            traces[traceId]['y'].append(dataPoint.value)
            traces[traceId]['x'].append(
                self.getX(dataPoint, xAxis, pointRef))
        return traces

    def traceId(self, pointRefence):
        if self._level == GraphTrial.L_DOSIS:
            return pointRefence.name
        else:
            return pointRefence.number

    def addTreatmentToReference(self, thesis):
        if thesis.id in self._references:
            return
        ttreatments = TreatmentThesis.getObjects(thesis)
        name = ''
        for ttreatment in ttreatments:
            if name is not None:
                name += ''
            name += ttreatment.treatment.getName()
        if name == '':
            name = thesis.name
        self._references[thesis.id] = name

    def getPointRefence(self, dataPoint):
        if self._level == GraphTrial.L_DOSIS:
            return dataPoint.thesis
        else:
            reference = None
            if self._level == GraphTrial.L_THESIS:
                reference = dataPoint.reference
            elif self._level == GraphTrial.L_REPLICA:
                reference = dataPoint.reference.thesis
            elif self._level == GraphTrial.L_SAMPLE:
                reference = dataPoint.reference.replica.thesis
            self.addTreatmentToReference(reference)
            return reference

    def getTraceName(self, pointRefence):
        if self._level == GraphTrial.L_DOSIS:
            return pointRefence.name
        else:
            return self._references[pointRefence.id]

    def getTraceColor(self, pointRefence):
        color = 1
        if self._level == GraphTrial.L_DOSIS:
            color = self._colors[pointRefence.name]
        else:
            color = pointRefence.number
        return GraphTrial.COLOR_LIST[color]

    def getTraceSymbol(self, pointRefence):
        symbol = 2
        if self._level == GraphTrial.L_DOSIS:
            symbol = self._colors[pointRefence.name]
        else:
            symbol = pointRefence.number
        return GraphTrial.SYMBOL_LIST[symbol]

    def assignColor(self, traceId):
        if self._level == GraphTrial.L_DOSIS:
            if traceId not in self._colors:
                number = len(list(self._colors.keys()))
                self._colors[traceId] = number + 1

    def prepareTrace(self, pointRef):
        return {
            'name': self.getTraceName(pointRef),
            'marker_color': self.getTraceColor(pointRef),
            'marker_symbol': self.getTraceSymbol(pointRef),
            'x': [],
            'y': []}

    def getX(self, dataPoint, xAxis, pointRef):
        if xAxis == GraphTrial.L_THESIS:
            return pointRef.name
        if xAxis == GraphTrial.L_DATE:
            return dataPoint.assessment.assessment_date
        if xAxis == GraphTrial.L_DAF:
            return dataPoint.assessment.daf
        if xAxis == GraphTrial.L_DOSIS:
            return dataPoint.dosis.rate

    def draw(self):
        if self._level == GraphTrial.L_DOSIS:
            return self._graph.line()
        elif self._level == GraphTrial.L_THESIS:
            return self._graph.bar()
        else:
            return self._graph.violin()
