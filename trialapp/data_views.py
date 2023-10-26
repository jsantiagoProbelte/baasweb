from baaswebapp.models import RateTypeUnit
from trialapp.models import Thesis, Replica, Sample, FieldTrial, \
    TreatmentThesis, PartRated
from trialapp.data_models import DataModel, ThesisData, \
    ReplicaData, Assessment, SampleData
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from rest_framework.views import APIView
from rest_framework.response import Response
from catalogue.models import UNTREATED
from baaswebapp.graphs import GraphTrial, EfficacyGraph, \
    COLOR_KEY_THESIS, COLOR_CONTROL, ColumnVariance
from trialapp.trial_analytics import AssessmentAnalytics, Abbott
from trialapp.trial_helper import TrialPermission
from baaswebapp.models import EventBaas, EventLog
from django.utils.translation import gettext_lazy as _


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
        value = request.POST['data-point'].replace(',', '.')
        refereceId = theIds[-2]
        # try to find if exists:
        if level == GraphTrial.L_THESIS:
            item = get_object_or_404(Thesis, pk=refereceId)
            ThesisData.setDataPoint(item, assessment, value)
        elif level == GraphTrial.L_REPLICA:
            item = get_object_or_404(Replica, pk=refereceId)
            ReplicaData.setDataPoint(item, assessment, value)
        elif level == GraphTrial.L_SAMPLE:
            if value == '':
                return Response({'success': False})
            sampleNumber = theIds[-1]
            item = Sample.findOrCreate(replica_id=refereceId,
                                       number=sampleNumber)
            SampleData.setDataPoint(item, assessment, value)
        else:
            return Response({'success': False}, status='500')
        EventLog.track(
                EventBaas.NEW_DATA,
                0,  # TODO request.user.id if request.user.id else 0,
                assessment.field_trial_id)
        return Response({'success': True})


class TrialDataApi(LoginRequiredMixin, DetailView):
    model = FieldTrial
    template_name = 'trialapp/trial_data.html'
    context_object_name = 'fieldTrial'
    _trial = None
    _assessments = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trial = self.get_object()
        dataAssHelper = DataTrialHelper(trial)
        permisions = TrialPermission(trial, self.request.user).getPermisions()
        assData = dataAssHelper.getTrialData()
        return {**context, **permisions, **{'dataContent': assData}}


class DataTrialHelper:
    def __init__(self, trial):
        self._trial = trial

    def getTrialData(self):
        self._assessments = Assessment.getObjects(
            self._trial, date_order=False)
        header = self.prepareHeader()
        showData = {'header': header, 'dataRows': self.preparaRows(),
                    'trialId': self._trial.id,
                    'ratedparts': [{'name':  _(item[1]), 'value': item[0]}
                                   for item in PartRated.choices],
                    'ratings': RateTypeUnit.getSelectList(asDict=True)}
        return showData

    def addValue(self, array, assessment, key, value):
        array.append({'name': key, 'value': value,
                      'id': assessment.id})

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
        rowspan = self._trial.repetitions
        rowNum = 0
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
            columnNum = 0
            for ass in self._assessments:
                value = dataPoints.get(ass.id, '')
                values.append({
                    'value': value,
                    'row': rowNum,
                    'column': columnNum,
                    'item_id': DataModel.generateDataPointId(
                        GraphTrial.L_REPLICA, ass, replica)})
                columnNum += 1
            rows.append(
                {'thesis': thesisName,
                 'rowspan': thisRowspan,
                 'replica': replica.name,
                 'color': replica.thesis.number,
                 'values': values})
            rowNum += 1
        return rows


# Show Data methods
class DataHelper:
    def __init__(self, assessment, editable=True):
        self._assessment = assessment
        self._trial = self._assessment.field_trial
        self._replicas = Replica.getFieldTrialObjects(self._trial)
        self._thesisTrial = Thesis.getObjects(self._trial, as_dict=True)
        self._numThesis = len(self._thesisTrial.keys())
        self._replicas_thesis = len(self._replicas) / self._numThesis
        self.findUntreated()
        self._editable = editable

    def findUntreated(self):
        self._untreated = 1  # number
        for thesisId in self._thesisTrial:
            thesis = self._thesisTrial[thesisId]
            treatments = TreatmentThesis.getObjects(thesis)
            for treat in treatments:
                if treat.treatment.name == UNTREATED:
                    self._untreated = thesis.number
                    return

    def whatLevelToShow(self):
        tData = ThesisData.objects.filter(
            assessment_id=self._assessment.id).count()
        rData = ReplicaData.objects.filter(
            assessment_id=self._assessment.id).count()
        sData = SampleData.objects.filter(
            assessment_id=self._assessment.id).count()

        if rData == 0 and tData == 0 and sData == 0:
            if self._trial.samples_per_replica > 0:
                return GraphTrial.L_SAMPLE + GraphTrial.L_REPLICA
            if self._trial.repetitions > 0:
                return GraphTrial.L_REPLICA
            else:
                return GraphTrial.L_THESIS

        if sData > 0:
            return GraphTrial.L_SAMPLE
        elif rData > 0:
            return GraphTrial.L_REPLICA
        else:
            return GraphTrial.L_THESIS

    def showDataAssessment(self):
        common = {}

        level = self.whatLevelToShow()
        if level == GraphTrial.L_THESIS:
            showData = self.prepareThesisBasedData()
        elif level == GraphTrial.L_REPLICA:
            showData = self.prepareReplicaBasedData()
        else:
            showReplicaInput = True
            if level == GraphTrial.L_SAMPLE:
                showReplicaInput = False
            samplesPerReplica = self._trial.samples_per_replica
            showData = self.prepareSampleBasedData(showReplicaInput,
                                                   samplesPerReplica)
            if samplesPerReplica == 0:
                # Maybe somehow data is imported and the value in trial is not
                # defined
                samplesPerReplica = len(showData['dataRows'][0]['sampleCols'])

            common['sampleNums'] = [i+1 for i in range(samplesPerReplica)]

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

    def buildOutput(self, level, points, stats, efficacyData, rows, snk):
        graph = GraphTrial.NO_DATA_AVAILABLE
        graphEfficacy = ''
        if points:
            graphHelper = DataGraphFactory(
                level, [self._assessment], points,
                showLegend=False, showXticklabels=False,
                references=self._thesisTrial)
            if 'Ratio Cq' in self._assessment.rate_type.unit:
                labels = {t.number: t.name
                          for t in list(self._thesisTrial.values())}
                graph = ColumnVariance.draw(snk, labels)
            else:
                graph = graphHelper.draw(type_graph=GraphTrial.VIOLIN)
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
            itemId = DataModel.genDataPointId(
                GraphTrial.L_THESIS,
                self._assessment.id, thesisId) if self._editable else None
            rows.append(
                {'thesis': thesisName, 'value': value,
                 'item_id': itemId,
                 'rowspan': 1, 'replica': None, 'color': nThesis})
            thesisValues.append(value)

        return self.buildOutput(GraphTrial.L_THESIS,
                                thesisPoints, None,
                                efficacyData,
                                rows, None)

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

        rowNumber = 0
        columnNumber = 0
        for replicaId in replicaList:
            value = ''
            if replicaId in replicaPointsDict:
                value = replicaPointsDict[replicaId]['value']
            lastThesis = self.addReplicaInfo(
                replicaNumberDict, value, replicaId, lastThesis,
                snk, efficacyData, rows, rowNumber, columnNumber)
            rowNumber += 1

        return self.buildOutput(GraphTrial.L_REPLICA,
                                replicaPoints,
                                stats['stats'] if stats else None,
                                efficacyData,
                                rows, snk)

    def addReplicaInfo(self, replicaNumberDict, value, replicaId, lastThesis,
                       snk, efficacyData, rows, rowNumber, columnNumber,
                       sampleCols=None,
                       genReplicaId=True):
        replicaName = replicaNumberDict[replicaId].name
        thesisId = replicaNumberDict[replicaId].thesis_id
        thesisNumber = self._thesisTrial[thesisId].number
        span = 0
        tvalue = ''
        groups = None
        if lastThesis != thesisNumber:
            lastThesis = thesisNumber
            span = self._replicas_thesis
            if snk and thesisNumber in snk:
                mean = snk[thesisNumber]['mean']
                if 'group' in snk[thesisNumber]:
                    groups = f"{', '.join(snk[thesisNumber]['group'])}"
                tvalue = mean
                efficacyData[thesisNumber] = mean
        rItemId = DataModel.genDataPointId(
            GraphTrial.L_REPLICA, self._assessment.id,
            replicaId) if genReplicaId and self._editable else None
        rows.append(
                {'thesis': self._thesisTrial[thesisId],
                 'tvalue': tvalue,
                 'value': value,
                 'groups': groups,
                 'item_id': rItemId,
                 'rowspan': span,
                 'row': rowNumber,
                 'column': columnNumber,
                 'replica': replicaName,
                 'color': thesisNumber,
                 'sampleCols': sampleCols})
        return lastThesis

    def genSampleColums(self, existingSamplesInReplica,
                        samplePointsDict, replicaId,
                        samplesPerReplica):
        sampleCols = []
        rValueAgg = 0
        rValueCount = 0
        sampleNums = list(existingSamplesInReplica.keys())
        sampleNums.sort()
        if samplesPerReplica > len(sampleNums):
            sampleNums = [i+1 for i in range(samplesPerReplica)]
        for sampleNum in sampleNums:
            sValue = ''
            sampleId = None
            if sampleNum in existingSamplesInReplica:
                sampleId = existingSamplesInReplica[sampleNum]
            if sampleId in samplePointsDict:
                sValue = samplePointsDict[sampleId]['value']
                rValueAgg += sValue
                rValueCount += 1
            itemId = DataModel.genDataPointId(
                GraphTrial.L_SAMPLE, self._assessment.id, replicaId,
                fakeId=sampleNum) if self._editable else None
            sampleCols.append({
                'value': sValue,
                'item_id': itemId})
        # For the Ratio Cq values, the mean has been calculated.
        rValue = None
        rValueDb = ReplicaData.objects.filter(
            assessment_id=self._assessment.id,
            reference_id=replicaId)
        if rValueDb:
            rValue = rValueDb[0].value
        else:
            if rValueCount > 1:
                rValue = round(rValueAgg / rValueCount, 2)
        return sampleCols, rValue

    def prepareSampleBasedData(self, showReplicaInput, samplesPerReplica):
        samplePoints = SampleData.dataPointsAssess([self._assessment.id])
        # We need to use reference__id because referece__number is not unique
        samplePointsDict = self.referencePointsDict(samplePoints,
                                                    'reference__id')
        replicaNumberDict, replicaList = self.replicaNumberDict()
        replicaSampleDict = Sample.replicaSampleDict(self._trial)

        stats = None
        efficacyData = {}
        if len(samplePoints) > 0:
            aa = AssessmentAnalytics(self._assessment, self._numThesis,
                                     isSampleData=True)
            aa.analyse(self._replicas, dataReplica=samplePoints)
            stats = aa.getStats()
        snk = stats['out'] if stats else None
        rows = []
        lastThesis = None

        rowNumber = 0
        columnNumber = 0
        for replicaId in replicaList:
            existingSamplesInReplica = {}
            if replicaId in replicaSampleDict:
                # we may not have all of them.
                existingSamplesInReplica = replicaSampleDict[replicaId]

            sampleCols, rValue = self.genSampleColums(
                existingSamplesInReplica,
                samplePointsDict, replicaId,
                samplesPerReplica)

            genReplicaId = False
            if not rValue:
                rValue = ''
                if showReplicaInput:
                    # We generate the form to input replica value
                    # if the samples are None and we allow to
                    # showReplicaInput, which is the first time
                    # we show a new assessment page
                    genReplicaId = True

            lastThesis = self.addReplicaInfo(
                replicaNumberDict, rValue, replicaId, lastThesis,
                snk, efficacyData, rows, rowNumber, columnNumber,
                sampleCols=sampleCols,
                genReplicaId=genReplicaId)
            rowNumber += 1

        return self.buildOutput(GraphTrial.L_SAMPLE,
                                samplePoints,
                                stats['stats'] if stats else None,
                                efficacyData,
                                rows, snk)


class DataGraphFactory():
    _level = None
    _graph = None
    _references = {}
    _colors = {}
    _controlNumber = None
    _keyThesisNumber = None

    def __init__(self, level, assessments,
                 dataPoints, xAxis=GraphTrial.L_DATE,
                 controlNumber=None, keyThesisNumber=None,
                 showLegend=True, showXticklabels=True,
                 showTitle=False, references=None):
        self._level = level
        self._showLegend = showLegend
        self._assessments = {item.id: item for item in assessments}
        self._references = references if references else {}
        self._colors = {}
        self._controlNumber = controlNumber
        self._keyThesisNumber = keyThesisNumber
        traces = self.buildData(dataPoints, xAxis)
        if len(traces) > 0:
            self._graph = GraphTrial(level, assessments[0].rate_type,
                                     assessments[0].getPartRated(),
                                     traces, xAxis=xAxis,
                                     showXticklabels=showXticklabels,
                                     showLegend=showLegend,
                                     showTitle=showTitle)
        else:
            self._graph = GraphTrial.NO_DATA_AVAILABLE

    def addLineColorsToTraces(self, keyThesisNumber, untreatedNumber):
        colorsDict = {keyThesisNumber: COLOR_KEY_THESIS,
                      untreatedNumber: COLOR_CONTROL}
        self._graph.addColorLinesToTraces(colorsDict)

    def addTrace(self, line, name):
        self._graph.addTrace(line, name)

    def getTitle(self):
        return self._graph._title

    def dataPointValue(self, dataPoint):
        if self._level in [GraphTrial.L_DOSIS, GraphTrial.L_DAF]:
            return dataPoint.value
        else:
            return dataPoint['value']

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
        elif self._level == GraphTrial.L_DAF:
            return pointRefence.number
        else:
            return self._references[pointRefence].number

    def getPointRefence(self, dataPoint):
        if self._level == GraphTrial.L_DOSIS:
            return dataPoint.thesis
        else:
            if self._level in GraphTrial.L_THESIS:
                return dataPoint['reference__id']
            elif self._level == GraphTrial.L_REPLICA:
                return dataPoint['reference__thesis__id']
            elif self._level == GraphTrial.L_SAMPLE:
                return dataPoint['reference__replica__thesis__id']
            return None

    def getTraceName(self, pointRefence):
        if self._level == GraphTrial.L_DOSIS:
            return pointRefence.name
        elif self._level == GraphTrial.L_DAF:
            return self._references[pointRefence.id]
        else:
            return self._references[pointRefence].name

    def getTraceColor(self, pointRefence):
        colorKey = self.traceId(pointRefence)
        if self._level == GraphTrial.L_DOSIS:
            colorKey = self._colors[colorKey]
        else:
            if self._controlNumber and self._controlNumber == colorKey:
                return COLOR_CONTROL
            if self._keyThesisNumber and self._keyThesisNumber == colorKey:
                return COLOR_KEY_THESIS
        return GraphTrial.COLOR_LIST[colorKey]

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
        trace = {
            'name': self.getTraceName(pointRef),
            'trace_color': self.getTraceColor(pointRef),
            'x': [],
            'y': []}
        if self._level == GraphTrial.L_SAMPLE:
            trace['marker_symbol'] = self.getTraceSymbol(pointRef)
        return trace

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
        if xAxis == GraphTrial.L_ASSMT:
            return dataPoint['assessment__number']

    def draw(self, type_graph=None):
        if type_graph:
            method = GraphTrial.DRAW_TYPE.get(type_graph)
        else:
            method = GraphTrial.DRAW_TYPE.get(type_graph,
                                              GraphTrial.violin)
        return method(self._graph)

    def drawConclusionGraph(self, num_assmts):
        typeFigure = GraphTrial.LINE if num_assmts > 1 else GraphTrial.BAR
        return self._graph.drawConclussionGraph(typeFigure=typeFigure)
