# Create your views here.
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Evaluation, Thesis, AssessmentUnit,\
                            TrialAssessmentSet, FieldTrial, Replica,\
                            ThesisData, ReplicaData, SampleData,\
                            AssessmentType, ModelHelpers
from django.shortcuts import get_object_or_404, render
from trialapp.trial_helper import LayoutTrial
from rest_framework.views import APIView
from rest_framework.response import Response
# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


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
            pk=request.POST['trial_assessment_set_id'])
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
            SampleData.setDataPoint(theIds[-2], evaluation, unit, value)
        else:
            return Response({'success': False})

        return Response({'success': True})


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


def showDataThesisIndex(request, evaluation_id=None,
                        errors=None):
    template_name = 'trialapp/data_thesis_index.html'
    evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
    thesisTrial = Thesis.getObjects(evaluation.field_trial)
    trialAssessmentSets = TrialAssessmentSet.getObjects(evaluation.field_trial)
    dataPoints = ThesisData.getDataPoints(evaluation)
    dataPointsList = sortDataPointsForDisplay(
        'thesis', evaluation, thesisTrial, trialAssessmentSets, dataPoints)
    return render(request, template_name, {
                  'evaluation': evaluation,
                  'dataPoints': dataPointsList,
                  'theses': thesisTrial,
                  'trialAssessmentSets': trialAssessmentSets,
                  'errors': errors})


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
    replicaDataSets = LayoutTrial.showLayout(
                        evaluation.field_trial,
                        evaluation,
                        thesisTrial)
    return render(request, template_name, {
                  'trialAssessmentSets': trialAssessmentSets,
                  'replicaDataSets': replicaDataSets,
                  'dataPoints': dataPointsList,
                  'evaluation': evaluation,
                  'theses': thesisTrial,
                  'errors': errors})
