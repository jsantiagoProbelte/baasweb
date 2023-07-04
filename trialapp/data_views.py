from baaswebapp.models import RateTypeUnit
from trialapp.models import Thesis, Replica, Sample, FieldTrial
from trialapp.data_models import DataModel, ThesisData,\
    ReplicaData, Assessment, SampleData
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from baaswebapp.graphs import GraphTrial, EfficacyGraph
from trialapp.trial_analytics import AssessmentAnalytics, Abbott


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
        self.findUntreated()

    def findUntreated(self):
        self._untreated = 1  # number

    def whatLevelToShow(self):
        tData = ThesisData.objects.filter(
            assessment_id=self._assessment.id).count()
        rData = ReplicaData.objects.filter(
            assessment_id=self._assessment.id).count()

        if rData == 0 and tData == 0:
            if self._trial.replicas_per_thesis > 0:
                return GraphTrial.L_REPLICA
            else:
                return GraphTrial.L_THESIS

        if rData > 0:
            return GraphTrial.L_REPLICA
        else:
            return GraphTrial.L_THESIS

    def showDataAssessment(self):
        common = {'title': self._assessment.getTitle(),
                  'assessment': self._assessment,
                  'fieldTrial': self._trial}

        level = self.whatLevelToShow()
        if level == GraphTrial.L_THESIS:
            showData = self.prepareThesisBasedData()
        if level == GraphTrial.L_REPLICA:
            showData = self.prepareReplicaBasedData()

        if showData:
            return {**showData, **common}
        else:
            return {**common, 'points': 0}

    def referencePointsDict(self, dataPoints, referenceKey):
        return {item[referenceKey]: item for item in dataPoints}

    def thesisNumberDict(self):
        thesisNumberDict = {self._thesisTrial[idT].number: idT
                            for idT in self._thesisTrial}
        thesisList = list(thesisNumberDict.keys())
        thesisList.sort()
        return thesisNumberDict, thesisList

    def replicaNumberDict(self):
        # _replicas is already ordered by thesis number and replica number
        replicaNumberDict = {}
        replicaList = []
        for replica in self._replicas:
            replicaNumberDict[replica.id] = replica
            replicaList.append(replica.id)
        return replicaNumberDict, replicaList

    def efficacyGraph(self, efficacyData):
        numNameDict = {}
        for ref in self._thesisTrial:
            thesis = self._thesisTrial[ref]
            numNameDict[thesis.number] = thesis.name
        efficacyValues = Abbott(self._untreated, efficacyData).run()
        if efficacyValues:
            return EfficacyGraph.draw(
                numNameDict,
                efficacyValues)
        else:
            return 'Cannot calculate efficacy.'

    def buildOutput(self, level, points, stats, efficacyData, rows):
        graph = GraphTrial.NO_DATA_AVAILABLE
        graphEfficacy = ''
        if points:
            graphHelper = DataGraphFactory(
                level, [self._assessment], points,
                references=self._thesisTrial)
            graph = graphHelper.draw()
        if efficacyData:
            graphEfficacy = self.efficacyGraph(efficacyData)
        return {'dataRows': rows,
                'graphData': graph,
                'efficacy': graphEfficacy,
                'stats': stats,
                'level': level,
                'points': len(points)}

    def prepareThesisBasedData(self):
        thesisPoints = ThesisData.dataPointsAssess([self._assessment.id])
        thesisPointsDict = self.referencePointsDict(thesisPoints,
                                                    'reference__number')
        thesisNumberDict, thesisList = self.thesisNumberDict()

        rows = []
        thesisValues = []
        efficacyData = {}
        for nThesis in thesisList:
            thesisId = thesisNumberDict[nThesis]
            if nThesis in thesisPointsDict:
                value = thesisPointsDict[nThesis]['value']
                efficacyData[nThesis] = value
                if thesisPointsDict[nThesis]['reference__id'] != thesisId:
                    return ''
            else:
                # assume item['reference__id'] =
                value = ''
            thesisName = self._thesisTrial[thesisId]
            rows.append(
                {'thesis': thesisName, 'value': value,
                 'item_id': DataModel.genDataPointId(
                    GraphTrial.L_THESIS, self._assessment.id, thesisId),
                 'rowspan': 1, 'replica': None, 'color': nThesis})
            thesisValues.append(value)

        return self.buildOutput(GraphTrial.L_THESIS,
                                thesisPoints, None,
                                efficacyData,
                                rows)

    def prepareReplicaBasedData(self):
        replicaPoints = ReplicaData.dataPointsAssess([self._assessment.id])
        replicaPointsDict = self.referencePointsDict(replicaPoints,
                                                     'reference__id')
        replicaNumberDict, replicaList = self.replicaNumberDict()
        stats = None
        efficacyData = {}
        if len(replicaPoints) > 0:
            aa = AssessmentAnalytics(self._assessment, self._numThesis)
            aa.analyse(self._replicas, dataReplica=replicaPoints)
            stats = aa.getStats()
        snk = stats['out'] if stats else None
        rows = []
        lastThesis = None

        for replicaId in replicaList:
            if replicaId in replicaPointsDict:
                value = replicaPointsDict[replicaId]['value']
                if replicaPointsDict[replicaId]['reference__id'] != replicaId:
                    return None
            else:
                # assume item['reference__id'] =
                value = ''
            replicaName = replicaNumberDict[replicaId].name

            thesisId = replicaNumberDict[replicaId].thesis_id
            thesisNumber = self._thesisTrial[thesisId].number
            span = 0
            tvalue = ''
            if lastThesis != thesisNumber:
                lastThesis = thesisNumber
                span = self._replicas_thesis
                if snk and thesisNumber in snk:
                    mean = snk[thesisNumber]['mean']
                    groups = ''
                    if 'group' in snk[thesisNumber]:
                        groups = ', '.join(snk[thesisNumber]['group'])
                    tvalue = f"{mean} "\
                             f"({groups})"
                    efficacyData[thesisNumber] = mean
            rows.append(
                {'thesis': self._thesisTrial[thesisId],
                 'tvalue': tvalue,
                 'value': value,
                 'item_id': DataModel.genDataPointId(
                    GraphTrial.L_REPLICA, self._assessment.id,
                    replicaId),
                 'rowspan': span,
                 'replica': replicaName,
                 'color': thesisNumber})

        return self.buildOutput(GraphTrial.L_REPLICA,
                                replicaPoints,
                                stats['stats'] if stats else None,
                                efficacyData,
                                rows)


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
            self._graph = GraphTrial.NO_DATA_AVAILABLE

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
