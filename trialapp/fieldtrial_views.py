# Create your views here.
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import Application, FieldTrial, Thesis
from django.shortcuts import render, get_object_or_404, redirect
from .forms import FieldTrialCreateForm

# class FieldTrialListView(LoginRequiredMixin, ListView):
#    login_url = '/login'


class FieldTrialListView(ListView):
    model = FieldTrial
    paginate_by = 100  # if pagination is desired

    def get_context_data(self, **kwargs):

        new_list = []

        for item in FieldTrial.getObjects():
            applications = Application.objects.filter(field_trial=item).count()
            thesis = Thesis.objects.filter(field_trial=item).count()

            new_list.append({
                'name': item.name,
                'crop': item.crop.name,
                'product': item.product.name,
                'project': item.project.name,
                'objective': item.objective.name,
                'plague': item.plague.name if item.plague else '',
                'id': item.id,
                'applications': applications,
                'thesis': thesis})

        return {'object_list': new_list}


def editNewFieldTrial(request, field_trial_id=None, errors=None):
    initialValues = {'field_trial_id': None}
    template_name = 'trialapp/fieldtrial_edit.html'
    title = 'New'
    if field_trial_id is not None:
        title = 'Edit'
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        initialValues = {
            'field_trial_id': fieldTrial.id,
            'name': fieldTrial.name,
            'phase': fieldTrial.phase.id,
            'objective': fieldTrial.objective.id,
            'responsible': fieldTrial.responsible,
            'product': fieldTrial.product.id,
            'crop': fieldTrial.crop.id,
            'plague': fieldTrial.plague.id,
            'initiation_date': fieldTrial.initiation_date,
            'completion_date': fieldTrial.completion_date,
            'farmer': fieldTrial.farmer,
            'location': fieldTrial.location,
            }
    elif 'name' in request.POST:
        # This is the flow in case of error
        initialValues = {
            'field_trial_id': field_trial_id,
            'name': request.POST['name'],
        }

    dictKwargs = FieldTrial.generateFormKwargsChoices(initialValues)
    newFieldTrial_form = FieldTrialCreateForm(**dictKwargs)

    return render(request, template_name,
                  {'create_form': newFieldTrial_form,
                   'title': title,
                   'errors': errors})


def saveFieldTrial(request, field_trial_id=None):
    values = {}
    foreignModels = FieldTrial.getForeignModels()
    for model in foreignModels:
        label = foreignModels[model]
        values[label] = model.objects.get(pk=request.POST[label])

    if 'field_trial_id' in request.POST and request.POST['field_trial_id']:
        # This is not a new user review.
        fieldTrial = get_object_or_404(FieldTrial,
                                       pk=request.POST['field_trial_id'])
        fieldTrial.name = FieldTrial.getValueFromRequestOrArray(
            request, values, 'name')
        fieldTrial.phase = FieldTrial.getValueFromRequestOrArray(
            request, values, 'phase')
        fieldTrial.objective = FieldTrial.getValueFromRequestOrArray(
            request, values, 'objective')
        fieldTrial.responsible = FieldTrial.getValueFromRequestOrArray(
            request, values, 'responsible')
        fieldTrial.product = FieldTrial.getValueFromRequestOrArray(
            request, values, 'product')
        fieldTrial.project = FieldTrial.getValueFromRequestOrArray(
            request, values, 'project')
        fieldTrial.crop = FieldTrial.getValueFromRequestOrArray(
            request, values, 'crop')
        fieldTrial.plague = FieldTrial.getValueFromRequestOrArray(
            request, values, 'plague')
        fieldTrial.initiation_date = FieldTrial.getValueFromRequestOrArray(
            request, values, 'initiation_date')
        fieldTrial.farmer = FieldTrial.getValueFromRequestOrArray(
            request, values, 'farmer')
        fieldTrial.location = FieldTrial.getValueFromRequestOrArray(
            request, values, 'location')
        # fieldTrial.completion_date = FieldTrial.getValueFromRequestOrArray(
        #     request, values,
        #     'completion_date')

    else:
        # This is a new field trial
        fieldTrial = FieldTrial(
            name=FieldTrial.getValueFromRequestOrArray(
                request, values, 'name'),
            phase=FieldTrial.getValueFromRequestOrArray(
                request, values, 'phase'),
            objective=FieldTrial.getValueFromRequestOrArray(
                request, values, 'objective'),
            responsible=FieldTrial.getValueFromRequestOrArray(
                request, values, 'responsible'),
            product=FieldTrial.getValueFromRequestOrArray(
                request, values, 'product'),
            project=FieldTrial.getValueFromRequestOrArray(
                request, values, 'project'),
            crop=FieldTrial.getValueFromRequestOrArray(
                request, values, 'crop'),
            plague=FieldTrial.getValueFromRequestOrArray(
                request, values, 'plague'),
            initiation_date=FieldTrial.getValueFromRequestOrArray(
                request, values, 'initiation_date'),
            farmer=FieldTrial.getValueFromRequestOrArray(
                request, values, 'farmer'),
            location=FieldTrial.getValueFromRequestOrArray(
                request, values, 'location')
        )
    fieldTrial.save()
    return redirect('fieldtrial-list')
