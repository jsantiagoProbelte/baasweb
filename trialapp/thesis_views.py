# Create your views here.
from django.views.generic.list import ListView
# from django.contrib.auth.mixins import LoginRequiredMixin
from trialapp.models import FieldTrial, Thesis
from django.shortcuts import get_object_or_404  # render,  redirect
# from .forms import FieldTrialCreateForm

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


# def editNewFieldTrial(request, field_trial_id=None, errors=None):
#     initialValues = {'field_trial_id': None}
#     template_name = 'trialapp/thesis_edit.html'
#     title = 'New'
#     if field_trial_id is not None:
#         title = 'Edit'
#         fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
#     else:
#         initialValues = {
#             'field_trial_id': fieldTrial.id,
#             'name': fieldTrial.name,
#             'phase': fieldTrial.phase.id,
#             'objective': fieldTrial.objective.id,
#             'responsible': fieldTrial.responsible,
#             'product': fieldTrial.product.id,
#             'crop': fieldTrial.crop.id,
#             'plague': fieldTrial.plague.id,
#             'initiation_date': fieldTrial.initiation_date,
#             'completion_date': fieldTrial.completion_date,
#             'farmer': fieldTrial.farmer,
#             'location': fieldTrial.location,
#             }

#     dictKwargs = FieldTrial.generateFormKwargsChoices(initialValues)
#     newFieldTrial_form = FieldTrialCreateForm(**dictKwargs)

#     return render(request, template_name,
#                   {'create_form': newFieldTrial_form,
#                    'title': title,
#                    'errors': errors})


# def getValueFromRequestOrArray(request, values, label):
#     if label in values:
#         return values[label]
#     else:
#         if label in request.POST:
#             return request.POST[label]
#         else:
#             return None


# def saveFieldTrial(request, field_trial_id=None):
#     values = {}
#     foreignModels = FieldTrial.getForeignModels()
#     for model in foreignModels:
#         label = foreignModels[model]
#         values[label] = model.objects.get(pk=request.POST[label])

#     if 'field_trial_id' in request.POST and request.POST['field_trial_id']:
#         # This is not a new user review.
#         fieldTrial = get_object_or_404(FieldTrial,
#                                        pk=request.POST['field_trial_id'])
#         fieldTrial.name = getValueFromRequestOrArray(request, values, 'name')
#         fieldTrial.phase = getValueFromRequestOrArray(request, values,
# 'phase')
#         fieldTrial.objective = getValueFromRequestOrArray(request, values,
#                                                           'objective')
#         fieldTrial.responsible = getValueFromRequestOrArray(request, values,
#                                                             'responsible')
#         fieldTrial.product = getValueFromRequestOrArray(request, values,
#                                                         'product')
#         fieldTrial.project = getValueFromRequestOrArray(request, values,
#                                                         'project')
#         fieldTrial.crop = getValueFromRequestOrArray(request, values, 'crop')
#         fieldTrial.plague = getValueFromRequestOrArray(request, values,
#                                                        'plague')
#         fieldTrial.initiation_date = getValueFromRequestOrArray(
#             request, values,
#             'initiation_date')
#         fieldTrial.farmer = getValueFromRequestOrArray(request, values,
#                                                        'farmer')
#         fieldTrial.location = getValueFromRequestOrArray(request, values,
#                                                          'location')
#         # fieldTrial.completion_date = getValueFromRequestOrArray(
#         #     request, values,
#         #     'completion_date')

#     else:
#         # This is a new field trial
#         fieldTrial = FieldTrial(
#             name=getValueFromRequestOrArray(request, values, 'name'),
#             phase=getValueFromRequestOrArray(request, values, 'phase'),
#             objective=getValueFromRequestOrArray(request, values, 'objective'),
#             responsible=getValueFromRequestOrArray(request, values,
#                                                    'responsible'),
#             product=getValueFromRequestOrArray(request, values, 'product'),
#             project=getValueFromRequestOrArray(request, values, 'project'),
#             crop=getValueFromRequestOrArray(request, values, 'crop'),
#             plague=getValueFromRequestOrArray(request, values, 'plague'),
#             initiation_date=getValueFromRequestOrArray(request, values,
#                                                        'initiation_date'),
#             farmer=getValueFromRequestOrArray(request, values, 'farmer'),
#             location=getValueFromRequestOrArray(request, values, 'location')
#         )
#     fieldTrial.save()
#     return redirect('fieldtrial-list')
