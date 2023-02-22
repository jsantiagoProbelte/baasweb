# Create your views here.
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import Evaluation, Thesis, AssessmentUnit,\
                            TrialAssessmentSet, FieldTrial, Replica,\
                            AssessmentType, Sample
from trialapp.data_models import DataModel, ThesisData, ReplicaData, SampleData
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
# from trialapp.fieldtrial_views import editNewFieldTrial
from baaswebapp.graphs import Graph


class ManageTrialAssessmentSet(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['delete', 'post']

    def post(self, request, format=None):
        field_trial_id = request.POST['field_trial_id'].split('-')[-1]
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        type_id = request.POST['assessment_type']
        assessmentType = get_object_or_404(AssessmentType, pk=type_id)
        unit_id = request.POST['assessment_unit']
        assessmentUnit = get_object_or_404(AssessmentUnit, pk=unit_id)

        assessmentUnitTrial = TrialAssessmentSet.objects.create(
            field_trial=fieldTrial,
            type=assessmentType,
            unit=assessmentUnit)
        responseData = {
            'id': assessmentUnitTrial.id,
            'type': assessmentType.name,
            'unit': assessmentUnit.name}
        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        item = TrialAssessmentSet.objects.get(
            pk=request.POST['item_id'])
        item.delete()
        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class SetDataEvaluation(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    def post(self, request, format=None):
        # noqa:                     5       4               3                   2              1
        # noqa: E501 data_point_id-[level]-[evaluation_id]-[assessment_set_id]-[reference_id]-[fakeId]
        theIds = request.POST['data_point_id'].split('-')
        level = theIds[-5]
        evaluation = get_object_or_404(Evaluation, pk=theIds[-4])
        unit = get_object_or_404(TrialAssessmentSet, pk=theIds[-3])
        value = request.POST['data-point']

        # try to find if exists:
        if level == Graph.L_THESIS:
            item = get_object_or_404(Thesis, pk=theIds[-2])
            ThesisData.setDataPoint(item, evaluation, unit, value)
        elif level == Graph.L_REPLICA:
            item = get_object_or_404(Replica, pk=theIds[-2])
            ReplicaData.setDataPoint(item, evaluation, unit, value)
        elif level == Graph.L_SAMPLE:
            replicaId = theIds[-2]
            sampleNumber = theIds[-1]
            item = Sample.findOrCreate(replica_id=replicaId,
                                       number=sampleNumber)
            SampleData.setDataPoint(item, evaluation, unit, value)
        else:
            return Response({'success': False}, status='500')
        return Response({'success': True})


@login_required
def showTrialAssessmentSetIndex(request, field_trial_id=None,
                                errors=None):
    template_name = 'trialapp/trial_assessment_set_index.html'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    trialAssessmentSets = TrialAssessmentSet.getObjects(fieldTrial)
    return render(request, template_name, {
                  'fieldTrial': fieldTrial,
                  'assessmentUnits': AssessmentUnit.getSelectList(asDict=True),
                  'assessmentTypes': AssessmentType.getSelectList(asDict=True),
                  'trialAssessmentSets': trialAssessmentSets,
                  'errors': errors})


# Show Data methods
class DataHelper:
    def __init__(self, evaluationId):
        self._evaluation = get_object_or_404(Evaluation, pk=evaluationId)
        self._fieldTrial = self._evaluation.field_trial
        self._replicas = Replica.getFieldTrialObjects(self._fieldTrial)
        self._thesisTrial = Thesis.getObjects(self._fieldTrial)
        self._trialAssessmentSets = TrialAssessmentSet.getObjects(
            self._fieldTrial)

    def prepareHeader(self, references):
        header = []
        lastIndex = "Bla"
        for reference in references:
            thisIndex = reference.getReferenceIndexDataInput()
            if lastIndex == thisIndex:
                thisIndex = ''
            else:
                lastIndex = thisIndex
            header.append({
                'index': thisIndex,
                'color': reference.getBackgroundColor(),
                'name': reference.getKey(),
                'id': reference.id})
        return header

    CLSDATAS = {
        Graph.L_REPLICA: ReplicaData,
        Graph.L_THESIS: ThesisData,
        Graph.L_SAMPLE: SampleData}

    def prepareDataPoints(self, references, level, assSet):
        clsData = DataHelper.CLSDATAS[level]
        dataPoints = clsData.getDataPointsAssSet(self._evaluation,
                                                 assSet)
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
                    level, self._evaluation, assSet, reference)})
        rows = [{
            'index': self._evaluation.evaluation_date,
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
                    self._evaluation, assSet, fakeSampleId)
                value = ''
                for dataPoint in dataPoints:
                    if dataPoint.reference.replica.id == replica.id:
                        value = dataPoint.value
                        dataPointsForGraph.append(dataPoint)
                        break
                dataPointsToDisplay.append({
                    'value': value,
                    'item_id': DataModel.generateDataPointId(
                        level, self._evaluation, assSet,
                        replica, fakeSampleId)})
            rows.append({
                'index': fakeSampleId,
                'dataPoints': dataPointsToDisplay})
        return rows, dataPointsForGraph

    def prepareAssSet(self, level, assSet,
                      references):
        graph = 'Add data and refresh to show graph'
        if level == Graph.L_SAMPLE:
            rows, pointForGraph = self.prepareSampleDataPoints(
                references, level, assSet)
        else:
            rows, pointForGraph = self.prepareDataPoints(
                references, level, assSet)
        # Calculate graph
        pointsInGraphs = len(pointForGraph)
        if pointsInGraphs > 1:
            graph = Graph(level, [assSet],
                          pointForGraph, showTitle=False)
            graphPlots, classGraph = graph.draw(level)
            # We only expect one
            graph = graphPlots[0][0]
        return rows, graph, pointsInGraphs

    TOKEN_LEVEL = {
        Graph.L_REPLICA: 'dataPointsR',
        Graph.L_THESIS: 'dataPointsT',
        Graph.L_SAMPLE: 'dataPointsS'}

    def showDataPerLevel(self, level, onlyThisData=False):
        references = None
        subtitle = 'Evaluation'
        if level == Graph.L_THESIS:
            references = self._thesisTrial
        elif level == Graph.L_REPLICA:
            references = self._replicas
        elif level == Graph.L_SAMPLE:
            references = self._replicas
            subtitle = 'Samples'
            if not self._fieldTrial.samples_per_replica:
                return {DataHelper.TOKEN_LEVEL[level]: [{
                    'errors': 'Number of samples per replica '
                              'is not defined. Go to field trial'
                              'definition'}]}, 0
        dataPointsList = []
        totalPoints = 0
        header = self.prepareHeader(references)
        for assSet in self._trialAssessmentSets:
            rows, graph, pointsInGraph = self.prepareAssSet(
                level, assSet, references)
            dataPointsList.append({
                'title': assSet.getName(), 'subtitle': subtitle,
                'header': header, 'errors': '',
                'graph': graph, 'rows': rows})
            totalPoints += pointsInGraph
        return self.returnData(
            {DataHelper.TOKEN_LEVEL[level]: dataPointsList},
            onlyThisData), totalPoints

    def returnData(self, dataToReturned, onlyThisData):
        if onlyThisData:
            return dataToReturned
        else:
            common = {
                'title': self._evaluation.getTitle(),
                'trialAssessmentSets': self._trialAssessmentSets,
                'assessment': self._evaluation,
                'theses': self._thesisTrial,
                'fieldTrial': self._fieldTrial}
            return {**common, **dataToReturned}

    def makeActiveView(self, pointsR, pointsT):
        active = Graph.L_SAMPLE
        if pointsR > 0:
            active = Graph.L_REPLICA
        elif pointsT > 0:
            active = Graph.L_THESIS
        activeViews = {}
        for level in Graph.LEVELS:
            navActive = ''
            tabActive = ''
            if level == active:
                navActive = 'active'
                tabActive = 'show active'
            activeViews['{}_nav'.format(level)] = navActive
            activeViews['{}_tab'.format(level)] = tabActive
        return activeViews

    def showDataEvaluation(self):
        dataR, pR = self.showDataPerLevel(Graph.L_REPLICA)
        dataT, pT = self.showDataPerLevel(Graph.L_THESIS, onlyThisData=True)
        dataS, pS = self.showDataPerLevel(Graph.L_SAMPLE, onlyThisData=True)
        activeViews = self.makeActiveView(pR, pT)
        return {**dataR, **dataT, **dataS, **activeViews}
