# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import FieldTrial,  ProductEvaluation,\
    ProductThesis, Evaluation, TrialAssessmentSet, ReplicaData,\
    ThesisData, SampleData
from django.shortcuts import get_object_or_404, render, redirect
from .forms import EvaluationEditForm
from rest_framework.views import APIView
from rest_framework.response import Response
from trialapp.trial_helper import LayoutTrial
from baaswebapp.graphs import Graph


class EvaluationListView(LoginRequiredMixin, ListView):
    model = Evaluation
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = None
        if 'field_trial_id' in self.request.GET:
            # for testing
            field_trial_id = self.request.GET['field_trial_id']
        elif 'field_trial_id' in self.kwargs:
            # from call on server
            field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Evaluation.getObjects(fieldTrial)

        trialAssessmentSets = TrialAssessmentSet.getObjects(fieldTrial)
        # Replica data
        dataPointsR = ReplicaData.getDataPointsFieldTrial(fieldTrial)
        graphR = Graph(Graph.L_REPLICA, trialAssessmentSets, dataPointsR)
        graphPlotsR, classGraphR = graphR.violin()

        # Thesis data
        dataPointsT = ThesisData.getDataPointsFieldTrial(fieldTrial)
        graphT = Graph(Graph.L_THESIS, trialAssessmentSets, dataPointsT)
        graphPlotsT, classGraphT = graphT.scatter()

        # Sample data
        dataPointsS = SampleData.getDataPointsFieldTrial(fieldTrial)
        graphS = Graph(Graph.L_SAMPLE, trialAssessmentSets, dataPointsS)
        graphPlotsS, classGraphS = graphS.violin()

        return {'object_list': new_list,
                'fieldTrial': fieldTrial,
                'graphPlotsR': graphPlotsR, 'classGraphR': classGraphR,
                'graphPlotsT': graphPlotsT, 'classGraphT': classGraphT,
                'graphPlotsS': graphPlotsS, 'classGraphS': classGraphS}


@login_required
def editEvaluation(request, field_trial_id=None, evaluation_id=None,
                   errors=None):
    initialValues = {'field_trial_id': field_trial_id,
                     'evaluation_id': evaluation_id}
    template_name = 'trialapp/evaluation_edit.html'
    title = 'New'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    product_list = []

    if evaluation_id is not None:
        title = 'Edit'
        evaluation = get_object_or_404(Evaluation, pk=evaluation_id)

        if fieldTrial.id != evaluation.field_trial.id:
            return redirect('fieldtrial-list', error='Bad forming Evaluation')

        initialValues['name'] = evaluation.name
        initialValues['evaluation_date'] = evaluation.evaluation_date
        initialValues['crop_stage_majority'] = evaluation.crop_stage_majority
        initialValues['crop_stage_scale'] = evaluation.crop_stage_scale
        # retrieve the list of the current defined product evaluation
        product_list = ProductEvaluation.getObjects(evaluation)

    edit_form = EvaluationEditForm(initial=initialValues)
    product_list_show = [{'id': item.id, 'name': item.getName()}
                         for item in product_list]

    return render(request, template_name,
                  {'edit_form': edit_form,
                   'fieldTrial': fieldTrial,
                   'evaluation_id': evaluation_id,
                   'title': title,
                   'product_list': product_list_show,
                   'products': ProductThesis.getSelectListFieldTrial(
                        fieldTrial, asDict=True),
                   'errors': errors})


@login_required
def saveEvaluation(request, evaluation_id=None):
    values = {}
    fieldTrial = get_object_or_404(
        FieldTrial, pk=request.POST['field_trial_id'])
    if 'evaluation_id' in request.POST and request.POST['evaluation_id']:
        # This is not a new user review.
        evaluation = get_object_or_404(
            Evaluation, pk=request.POST['evaluation_id'])
        evaluation.field_trial = fieldTrial
        evaluation.name = Evaluation.getValueFromRequestOrArray(
            request, values, 'name')
        evaluation.evaluation_date = Evaluation.getValueFromRequestOrArray(
            request, values, 'evaluation_date')
        evaluation.crop_stage_majority =\
            Evaluation.getValueFromRequestOrArray(
                request, values, 'crop_stage_majority')
        evaluation.crop_stage_scale = Evaluation.getValueFromRequestOrArray(
            request, values, 'crop_stage_scale')
        evaluation.save()
    else:
        # This is a new evaluation
        evaluation = Evaluation.objects.create(
            name=Evaluation.getValueFromRequestOrArray(
                request, values, 'name'),
            field_trial=fieldTrial,
            evaluation_date=Evaluation.getValueFromRequestOrArray(
                request, values, 'evaluation_date'),
            crop_stage_majority=Evaluation.getValueFromRequestOrArray(
                request, values, 'crop_stage_majority'),
            crop_stage_scale=Evaluation.getValueFromRequestOrArray(
                request, values, 'crop_stage_scale'))

        # Create by default a list based on all the existing thesis
        # and let the user remove them
        for item in ProductThesis.getObjectsPerFieldTrial(fieldTrial):
            ProductEvaluation.objects.create(
                product_thesis=item,
                thesis=item.thesis,
                evaluation=evaluation)

    return redirect(
        'evaluation-edit',
        field_trial_id=fieldTrial.id,
        evaluation_id=evaluation.id)


class ManageProductToEvaluation(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['delete', 'post']

    def post(self, request, format=None):
        evaluation_id = request.POST['evaluation_id'].split('-')[-1]
        evaluation = get_object_or_404(Evaluation, pk=evaluation_id)
        product_id = request.POST['product']
        productThesis = get_object_or_404(ProductThesis, pk=product_id)

        productEvaluation = ProductEvaluation(
            evaluation=evaluation,
            product_thesis=productThesis,
            thesis=productThesis.thesis)
        productEvaluation.save()
        responseData = {
            'id': productEvaluation.id,
            'name': productThesis.getName()}
        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        productEvaluation = ProductEvaluation.objects.get(
            pk=request.POST['item_id'])
        productEvaluation.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class AssessmentApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['delete']

    def delete(self, request, *args, **kwargs):
        item = Evaluation.objects.get(
            pk=request.POST['item_id'])
        fieldTrial = item.field_trial
        item.delete()

        LayoutTrial.distributeLayout(fieldTrial)
        response_data = {'msg': 'Thesis was deleted.'}
        return Response(response_data, status=200)
