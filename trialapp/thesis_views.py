# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
# from rest_framework import permissions
from trialapp.models import FieldTrial, Product, ProductThesis, RateUnit,\
    Thesis, Replica
from django.shortcuts import get_object_or_404, render, redirect
from .forms import ThesisEditForm
from rest_framework.views import APIView
from rest_framework.response import Response
from trialapp.trial_helper import FactoryTrials
from trialapp.trial_helper import LayoutTrial


class ThesisListView(LoginRequiredMixin, ListView):
    model = Thesis
    paginate_by = 100  # if pagination is desired
    login_url = '/login'

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Thesis.getObjects(fieldTrial)
        return {'object_list': new_list,
                'fieldTrial': fieldTrial,
                'rowsReplicas': LayoutTrial.showLayout(fieldTrial,
                                                       None,
                                                       new_list)}


@login_required
def editThesis(request, field_trial_id=None, thesis_id=None, errors=None):
    template_name = 'trialapp/thesis_edit.html'
    title = 'New'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    initialValues = {'field_trial_id': field_trial_id,
                     'thesis_id': thesis_id,
                     'number': Thesis.computeNumber(fieldTrial, True)}
    product_list = []
    replica_list = []

    if thesis_id is not None:
        title = 'Edit'
        thesis = get_object_or_404(Thesis, pk=thesis_id)

        if fieldTrial.id != thesis.field_trial.id:
            return redirect('fieldtrial-list', error='Bad forming Thesis')

        initialValues['name'] = thesis.name
        initialValues['number'] = thesis.number
        initialValues['description'] = thesis.description
        initialValues['number_applications'] = thesis.number_applications
        initialValues['interval'] = thesis.interval
        initialValues['first_application'] = thesis.first_application
        initialValues['mode'] = thesis.mode.id if thesis.mode else None
        product_list = ProductThesis.getObjects(thesis)
        replica_list = Replica.getObjects(thesis)

    dictKwargs = Thesis.generateFormKwargsChoices(initialValues)
    edit_form = ThesisEditForm(**dictKwargs)

    return render(request, template_name,
                  {'edit_form': edit_form,
                   'fieldTrial': fieldTrial,
                   'thesis_id': thesis_id,
                   'title': title,
                   'product_list': product_list,
                   'replica_list': replica_list,
                   'products': Product.getSelectList(asDict=True),
                   'rate_units': RateUnit.getSelectList(asDict=True),
                   'errors': errors})


@login_required
def saveThesis(request):
    fieldTrial = get_object_or_404(
        FieldTrial, pk=request.POST['field_trial_id'])
    values = Thesis.preloadValues(request.POST)
    if 'thesis_id' in request.POST and request.POST['thesis_id']:
        # This is not a new user review.
        thesis = get_object_or_404(
            Thesis, pk=request.POST['thesis_id'])
        thesis.field_trial = fieldTrial
        thesis.name = Thesis.getValueFromRequestOrArray(
            request, values, 'name')
        thesis.number = Thesis.getValueFromRequestOrArray(
            request, values, 'number')
        thesis.description = Thesis.getValueFromRequestOrArray(
            request, values, 'description')

        thesis.number_applications = Thesis.getValueFromRequestOrArray(
            request, values, 'number_applications', intValue=True)

        thesis.interval = Thesis.getValueFromRequestOrArray(
            request, values, 'interval', intValue=True)

        thesis.first_application = Thesis.getValueFromRequestOrArray(
            request, values, 'first_application', returnNoneIfEmpty=True)

        thesis.mode = Thesis.getValueFromRequestOrArray(
            request, values, 'mode', returnNoneIfEmpty=True)
        thesis.save()
    else:
        thesis = FactoryTrials.createThesisReplicasLayout(
            request, values, fieldTrial)

    return redirect('thesis-edit',
                    field_trial_id=fieldTrial.id,
                    thesis_id=thesis.id)


class ManageProductToThesis(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

    def post(self, request, format=None):
        thesis_id = request.POST['thesis_id'].split('-')[-1]
        thesis = get_object_or_404(Thesis, pk=thesis_id)
        product_id = request.POST['product']
        product = get_object_or_404(Product, pk=product_id)
        rate = request.POST['rate']
        rate_unit_id = request.POST['rate_unit']
        rateUnit = get_object_or_404(RateUnit, pk=rate_unit_id)

        productThesis = ProductThesis(
            thesis=thesis,
            product=product,
            rate_unit=rateUnit,
            rate=rate)
        productThesis.save()
        responseData = {
            'id': productThesis.id,
            'product': product.name,
            'rate_unit': rateUnit.name,
            'rate': rate}
        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        productThesis = ProductThesis.objects.get(
            pk=request.POST['item_id'])
        productThesis.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class ManageReplicaToThesis(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = [
        'delete', 'post']

    def post(self, request, format=None):
        thesis_id = request.POST['thesis_id'].split('-')[-1]
        thesis = get_object_or_404(Thesis, pk=thesis_id)
        count = Replica.objects.filter(thesis=thesis).count()
        replica = Replica.objects.create(
            thesis=thesis,
            pos_x=0,
            pos_y=0,
            number=count+1)

        responseData = {
            'id': replica.id,
            'pos_x': replica.pos_x,
            'pos_y': replica.pos_y,
            'number': replica.number}

        return Response(responseData)

    def delete(self, request, *args, **kwargs):
        replica = Replica.objects.get(
            pk=request.POST['replica_id'])
        replica.delete()

        response_data = {'msg': 'Product was deleted.'}
        return Response(response_data, status=200)


class ThesisApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['delete']

    def delete(self, request, *args, **kwargs):
        item = Thesis.objects.get(
            pk=request.POST['item_id'])
        item.delete()

        response_data = {'msg': 'Thesis was deleted.'}
        return Response(response_data, status=200)
