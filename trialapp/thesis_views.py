# Create your views here.
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial, Product, ProductThesis, RateUnit,\
    Thesis
from django.shortcuts import get_object_or_404, render, redirect
from .forms import ThesisEditForm
from rest_framework.views import APIView
from rest_framework.response import Response

# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


class ThesisListView(ListView):
    model = Thesis
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Thesis.getObjects(fieldTrial)
        return {'object_list': new_list,
                'field_trial_name': fieldTrial.name,
                'field_trial_id': fieldTrial.id}


def editThesis(request, field_trial_id=None, thesis_id=None, errors=None):
    initialValues = {'field_trial_id': field_trial_id, 'thesis_id': thesis_id}
    template_name = 'trialapp/thesis_edit.html'
    title = 'New'
    fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
    product_list = []

    if thesis_id is not None:
        title = 'Edit'
        thesis = get_object_or_404(Thesis, pk=thesis_id)

        if fieldTrial.id != thesis.field_trial.id:
            return redirect('fieldtrial-list', error='Bad forming Thesis')

        initialValues['name'] = thesis.name
        initialValues['number'] = thesis.number
        initialValues['description'] = thesis.description
        product_list = ProductThesis.getObjects(thesis)

    edit_form = ThesisEditForm(initial=initialValues)

    return render(request, template_name,
                  {'edit_form': edit_form,
                   'field_trial_id': field_trial_id,
                   'field_trial_name': fieldTrial.name,
                   'thesis_id': thesis_id,
                   'title': title,
                   'product_list': product_list,
                   'products': Product.getSelectList(asDict=True),
                   'rate_units': RateUnit.getSelectList(asDict=True),
                   'errors': errors})


def saveThesis(request, thesis_id=None):
    values = {}
    fieldTrial = get_object_or_404(
        FieldTrial, pk=request.POST['field_trial_id'])
    if 'thesis_id' in request.POST and request.POST['thesis_id']:
        # This is not a new user review.
        thesis = get_object_or_404(
            Thesis, pk=request.POST['field_trial_id'])
        thesis.field_trial = fieldTrial
        thesis.name = Thesis.getValueFromRequestOrArray(
            request, values, 'name')
        thesis.number = Thesis.getValueFromRequestOrArray(
            request, values, 'number')
        thesis.description = Thesis.getValueFromRequestOrArray(
            request, values, 'description')
    else:
        # This is a new field trial
        thesis = Thesis(
            name=Thesis.getValueFromRequestOrArray(
                request, values, 'name'),
            number=Thesis.getValueFromRequestOrArray(
                request, values, 'number'),
            field_trial=fieldTrial,
            description=Thesis.getValueFromRequestOrArray(
                request, values, 'description')
        )
    thesis.save()
    return redirect(
        'thesis-edit',
        field_trial_id=fieldTrial.id,
        thesis_id=thesis.id)


class AddProductToThesis(APIView):
    authentication_classes = []
    permission_classes = []

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
            'product': product.name,
            'rate_unit': rateUnit.name,
            'rate': rate}
        return Response(responseData)
