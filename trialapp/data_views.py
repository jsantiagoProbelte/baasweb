from baaswebapp.models import RateTypeUnit
from trialapp.models import Thesis, Replica, Sample, FieldTrial,\
    TreatmentThesis
from trialapp.data_models import DataModel, ThesisData,\
    ReplicaData, Assessment, SampleData
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from baaswebapp.graphs import GraphTrial
from trialapp.trial_analytics import AssessmentAnalytics


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

            partRated = ass.getPartRated()
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
        self._trial = self._assessment.field_trial
        self._replicas = Replica.getFieldTrialObjects(self._trial)
        self._thesisTrial = Thesis.getObjects(self._trial, as_dict=True)
        self._numThesis = len(self._thesisTrial.keys())
        self._replicas_thesis = len(self._replicas) / self._numThesis

    def showDataAssessment(self):
        common = {
                'title': self._assessment.getTitle(),
                'assessment': self._assessment,
                'fieldTrial': self._trial}
        showData = self.prepareThesisBasedData()
        if showData is None:
            showData = self.prepareReplicaBasedData()
        if showData:
            return {**showData, **common}
        else:
            return {**common, 'points': 0}

    def prepareThesisBasedData(self):
        thesisPoints = ThesisData.dataPointsAssess([self._assessment.id])
        if not thesisPoints:
            return None
        rows = []
        for item in thesisPoints:
            thesisNumber = item['reference__number']
            rows.append(
                {'thesis': self._thesisTrial[thesisNumber],
                 'tvalue': item['value'],
                 'rvalue': None,
                 'item_id': DataModel.genDataPointId(
                    GraphTrial.L_THESIS, self._assessment.id,
                    item['reference__id']),
                 'rowspan': 1,
                 'replica': None,
                 'color': thesisNumber})
        graphHelper = DataGraphFactory(
            GraphTrial.L_THESIS, [self._assessment], thesisPoints,
            references=self._thesisTrial)
        graph = graphHelper.draw()
        return {'dataRows': rows, 'graphData': graph,
                'stats': None,
                'level': GraphTrial.L_THESIS,
                'points': len(thesisPoints)}

    def prepareReplicaBasedData(self):
        replicaPoints = ReplicaData.dataPointsAssess([self._assessment.id])
        if not replicaPoints:
            return None
        stats = None
        if len(replicaPoints) == len(self._replicas):
            aa = AssessmentAnalytics(self._assessment, self._numThesis)
            aa.analyse(self._replicas, dataReplica=replicaPoints)
            stats = aa.getStats()
        snk = stats['snk'] if stats else None
        rows = []
        lastThesis = None

        for item in replicaPoints:
            thesisId = item['reference__thesis__id']
            thesisNumber = item['reference__thesis__number']
            span = 0
            tvalue = ''
            if lastThesis != thesisNumber:
                lastThesis = thesisNumber
                span = self._replicas_thesis
                if snk:
                    groups = ', '.join(snk[thesisNumber]['group'])
                    tvalue = f"{snk[thesisNumber]['mean']} "\
                             f"({groups})"
            rows.append(
                {'thesis': self._thesisTrial[thesisId],
                 'tvalue': tvalue,
                 'rvalue': item['value'],
                 'item_id': DataModel.genDataPointId(
                    GraphTrial.L_REPLICA, self._assessment.id,
                    item['reference__id']),
                 'rowspan': span,
                 'replica': item['reference__name'],
                 'color': thesisNumber})
        graphHelper = DataGraphFactory(
            GraphTrial.L_REPLICA, [self._assessment], replicaPoints,
            references=self._thesisTrial)
        graph = graphHelper.draw()
        return {'dataRows': rows, 'graphData': graph,
                'stats': stats['stats'] if stats else None,
                'level': GraphTrial.L_REPLICA,
                'points': len(replicaPoints)}


class DataGraphFactory():
    _level = None
    _graph = None
    _references = {}
    _colors = {}

    def __init__(self, level, assessments,
                 dataPoints, xAxis=GraphTrial.L_DATE,
                 showTitle=True, references=None):
        self._level = level
        self._assessments = {item.id: item for item in assessments}
        self._references = references if references else {}
        self._colors = {}
        traces = self.buildData(dataPoints, xAxis)
        if len(traces) > 0:
            self._graph = GraphTrial(level, assessments[0].rate_type,
                                     assessments[0].getPartRated(),
                                     traces, xAxis=xAxis,
                                     showTitle=showTitle)
        else:
            self._graph = 'No data points found'

    def dataPointValue(self, dataPoint):
        if self._level in [GraphTrial.L_REPLICA, GraphTrial.L_THESIS]:
            return dataPoint['value']
        else:
            return dataPoint.value

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
            traces[traceId]['y'].append(
                self.dataPointValue(dataPoint))
            traces[traceId]['x'].append(
                self.getX(dataPoint, xAxis, pointRef))
        return traces

    def traceId(self, pointRefence):
        if self._level == GraphTrial.L_DOSIS:
            return pointRefence.name
        elif self._level in [GraphTrial.L_THESIS, GraphTrial.L_REPLICA]:
            return self._references[pointRefence].number
        else:
            return pointRefence.number

    # To Delete
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
            if self._level in GraphTrial.L_THESIS:
                return dataPoint['reference__id']
            elif GraphTrial.L_REPLICA:
                return dataPoint['reference__thesis__id']
            elif self._level == GraphTrial.L_SAMPLE:
                return dataPoint.reference.replica.thesis
            return None

    def getTraceName(self, pointRefence):
        if self._level == GraphTrial.L_DOSIS:
            return pointRefence.name
        elif self._level in [GraphTrial.L_THESIS, GraphTrial.L_REPLICA]:
            return self._references[pointRefence].name
        else:
            return self._references[pointRefence.id]

    def getTraceColor(self, pointRefence):
        color = self.traceId(pointRefence)
        if self._level == GraphTrial.L_DOSIS:
            color = self._colors[color]
        return GraphTrial.COLOR_LIST[color]

    def getTraceSymbol(self, pointRefence):
        symbol = self.traceId(pointRefence)
        if self._level == GraphTrial.L_DOSIS:
            symbol = self._colors[symbol]
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
            assId = dataPoint['assessment__id']
            return self._assessments[assId].assessment_date
        if xAxis == GraphTrial.L_DAF:
            assId = dataPoint['assessment__id']
            return self._assessments[assId].daf
        if xAxis == GraphTrial.L_DOSIS:
            return dataPoint.dosis.rate

    def draw(self):
        if self._level == GraphTrial.L_DOSIS:
            return self._graph.line()
        elif self._level == GraphTrial.L_THESIS:
            return self._graph.bar()
        else:
            return self._graph.violin()
