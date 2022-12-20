# Create your views here.
from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import Evaluation, Thesis, AssessmentUnit,\
                            TrialAssessmentSet, FieldTrial, Replica,\
                            ThesisData, ReplicaData, SampleData,\
                            AssessmentType, ModelHelpers, Sample
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from trialapp.fieldtrial_views import editNewFieldTrial
from baaswebapp.graphs import Graph


class ManageTrialAssessmentSet(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

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
        # data_point_id-[evaluation_id]-[reference_id]-[assessment_set_id]
        theIds = request.POST['data_point_id'].split('-')
        level = theIds[-4]
        evaluation = get_object_or_404(Evaluation, pk=theIds[-3])
        unit = get_object_or_404(TrialAssessmentSet, pk=theIds[-1])
        value = request.POST['data-point']

        # try to find if exists:
        if level == 'thesis':
            item = get_object_or_404(Thesis, pk=theIds[-2])
            ThesisData.setDataPoint(item, evaluation, unit, value)
        elif level == 'replica':
            item = get_object_or_404(Replica, pk=theIds[-2])
            ReplicaData.setDataPoint(item, evaluation, unit, value)
        elif level == 'sample':
            item = get_object_or_404(Sample, pk=theIds[-2])
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


def sortDataPointsForDisplay(level, evaluation, references,
                             trialAssessments, dataPoints):
    # This is for diplay purposes. [[,],[,]...]
    # It has to follow the order of references
    # and then trial assessments
    values = []
    lastIndex = 'Nada'
    for reference in references:
        thisIndex = reference.getReferenceIndexDataInput()
        if lastIndex == thisIndex:
            thisIndex = ''
        else:
            lastIndex = thisIndex
        thisRefValues = {
            'index': thisIndex,
            'color': reference.getBackgroundColor(),
            'name': reference.getKey(),
            'id': reference.id,
            'dataPoints': []}
        for unit in trialAssessments:
            value = ''
            thisRefValue = {}
            thisRefValue['item_id'] = ModelHelpers.generateDataPointId(
                level, evaluation, reference, unit)
            for dataPoint in dataPoints:
                if dataPoint.reference.id == reference.id and\
                   unit.id == dataPoint.unit.id:
                    value = dataPoint.value
                    break
            thisRefValue['value'] = value
            thisRefValues['dataPoints'].append(thisRefValue)
        values.append(thisRefValues)
    return values


@login_required
def showDataThesisIndex(request, evaluation_id=None,
                        errors=None):
    template_name = 'trialapp/data_thesis_index.html'
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    thesisTrial = Thesis.getObjects(evaluation.field_trial)
    trialAssessmentSets = TrialAssessmentSet.getObjects(evaluation.field_trial)
    dataPoints = ThesisData.getDataPoints(evaluation)

    dataPointsList = sortDataPointsForDisplay(
        'thesis', evaluation, thesisTrial, trialAssessmentSets, dataPoints)

    graph = Graph(Graph.L_THESIS, trialAssessmentSets, dataPoints)
    graphPlots, classGraph = graph.bar()

    return render(request, template_name, {
                  'evaluation': evaluation,
                  'dataPoints': dataPointsList,
                  'theses': thesisTrial,
                  'graphPlots': graphPlots,
                  'classGraph': classGraph,
                  'trialAssessmentSets': trialAssessmentSets,
                  'errors': errors})


@login_required
def showDataReplicaIndex(request, evaluation_id=None,
                         errors=None):
    template_name = 'trialapp/data_replica_index.html'
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    replicas = Replica.getFieldTrialObjects(evaluation.field_trial)
    thesisTrial = Thesis.getObjects(evaluation.field_trial)
    trialAssessmentSets = TrialAssessmentSet.getObjects(evaluation.field_trial)
    dataPoints = ReplicaData.getDataPoints(evaluation)
    dataPointsList = sortDataPointsForDisplay(
        'replica', evaluation, replicas, trialAssessmentSets, dataPoints)

    graph = Graph(Graph.L_REPLICA, trialAssessmentSets, dataPoints)
    graphPlots, classGraph = graph.scatter()

    return render(request, template_name, {
                  'trialAssessmentSets': trialAssessmentSets,
                  'dataPoints': dataPointsList,
                  'evaluation': evaluation,
                  'theses': thesisTrial,
                  'graphPlots': graphPlots, 'classGraph': classGraph,
                  'errors': errors})


def needToRedirectToDefineSamples(request, fieldTrial):
    if fieldTrial.samples_per_replica == 0:
        return editNewFieldTrial(
            request,
            field_trial_id=fieldTrial.id,
            errors='You need to define the number of samples per replica')
    return None


def needToCreateSamples(request, replica):
    fieldTrial = replica.thesis.field_trial
    samples = Sample.getObjects(replica)
    if len(samples) > 0:
        # If there are samples, we are good to go
        return None, samples

    redirection = needToRedirectToDefineSamples(
        request, fieldTrial)
    if redirection:
        # if there are no samples because they are not defined
        # in the field trial, we will ask to define such number
        return redirection, None

    # If there were not created we do it in the spot
    Sample.createSamples(replica, fieldTrial.samples_per_replica)
    samples = Sample.getObjects(replica)
    return None, samples


@login_required
def showDataSamplesIndex(request, evaluation_id=None,
                         selected_replica_id=None, errors=None):
    template_name = 'trialapp/data_samples_index.html'
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    redirection = needToRedirectToDefineSamples(
        request, evaluation.field_trial)
    if redirection:
        return redirection
    replicas = Replica.getFieldTrialObjects(evaluation.field_trial)

    thesisTrial = Thesis.getObjects(evaluation.field_trial)
    trialAssessmentSets = TrialAssessmentSet.getObjects(evaluation.field_trial)
    dataPointsList = []
    selectedReplicaName = None
    missing_samples = False
    dataPoints = []
    if selected_replica_id is None or selected_replica_id == 0:
        pass
    else:
        replica = get_object_or_404(Replica, pk=selected_replica_id)
        selectedReplicaName = replica.getTitle()
        redirection, samples = needToCreateSamples(
            request, replica)
        if redirection:
            return redirection

        dataPoints = SampleData.getDataPointsReplica(evaluation, replica)
        dataPointsList = sortDataPointsForDisplay(
            'sample', evaluation, samples,
            trialAssessmentSets, dataPoints)

    replicaReferences = sortDataPointsForDisplay(
        'replicas', evaluation, replicas, trialAssessmentSets, [])

    allDataPoints = SampleData.getDataPoints(evaluation)
    graph = Graph(Graph.L_SAMPLE, trialAssessmentSets, allDataPoints)
    graphPlots, classGraph = graph.scatter()

    return render(request, template_name, {
                  'replicaReferences': replicaReferences,
                  'selectedReplicaName': selectedReplicaName,
                  'trialAssessmentSets': trialAssessmentSets,
                  'dataPoints': dataPointsList,
                  'evaluation': evaluation,
                  'theses': thesisTrial,
                  'missing_samples': missing_samples,
                  'graphPlots': graphPlots, 'classGraph': classGraph,
                  'errors': errors})
