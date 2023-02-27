# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from trialapp.models import FieldTrial, Evaluation, TrialAssessmentSet
from trialapp.data_models import ThesisData, ReplicaData, SampleData
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView

from baaswebapp.graphs import Graph
from trialapp.data_views import DataHelper
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.forms import MyDateInput


class AssessmentListView(LoginRequiredMixin, ListView):
    model = Evaluation
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'trialapp/assessment_list.html'

    def get_context_data(self, **kwargs):
        field_trial_id = None
        # from call on server
        field_trial_id = self.kwargs['field_trial_id']
        fieldTrial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Evaluation.getObjects(fieldTrial)

        trialAssessmentSets = TrialAssessmentSet.getObjects(fieldTrial)
        # Replica data
        dataPointsR = ReplicaData.getDataPointsFieldTrial(fieldTrial)
        graphR = Graph(Graph.L_REPLICA, trialAssessmentSets, dataPointsR,
                       xAxis=Graph.L_DATE)
        graphPlotsR, classGraphR = graphR.violin()

        # Thesis data
        dataPointsT = ThesisData.getDataPointsFieldTrial(fieldTrial)
        graphT = Graph(Graph.L_THESIS, trialAssessmentSets, dataPointsT,
                       xAxis=Graph.L_DATE)
        graphPlotsT, classGraphT = graphT.scatter()

        show_active_replica = 'show active'
        show_active_thesis = ''
        active_replica = 'active'
        active_thesis = ''
        if dataPointsT.count() > 0:
            show_active_thesis = 'show active'
            show_active_replica = ''
            active_replica = ''
            active_thesis = 'active'

        # Sample data
        dataPointsS = SampleData.getDataPointsFieldTrial(fieldTrial)
        graphS = Graph(Graph.L_SAMPLE, trialAssessmentSets, dataPointsS,
                       xAxis=Graph.L_DATE)
        graphPlotsS, classGraphS = graphS.violin()

        return {'object_list': new_list,
                'fieldTrial': fieldTrial,
                'show_active_thesis': show_active_thesis,
                'show_active_replica': show_active_replica,
                'active_replica': active_replica,
                'active_thesis': active_thesis,
                'graphPlotsR': graphPlotsR, 'classGraphR': classGraphR,
                'graphPlotsT': graphPlotsT, 'classGraphT': classGraphT,
                'graphPlotsS': graphPlotsS, 'classGraphS': classGraphS}


class AssessmentFormLayout(FormHelper):
    def __init__(self, new=True):
        super().__init__()
        title = 'New Assessment' if new else 'Edit Assessment'
        submitTxt = 'Create' if new else 'Save'
        self.add_layout(Layout(Div(
            HTML(title), css_class="h4 mt-4"),
            Div(Field('name', css_class='mb-3'),
                Field('evaluation_date', css_class='mb-3'),
                Field('crop_stage_majority', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
            ))


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ('name', 'crop_stage_majority', 'evaluation_date')

    def __init__(self, *args, **kwargs):
        super(AssessmentForm, self).__init__(*args, **kwargs)
        self.fields['evaluation_date'].widget = MyDateInput()
        self.fields['crop_stage_majority'].label = 'Crop Stage Majority (BBCH)'


class AssessmentCreateView(LoginRequiredMixin, CreateView):
    model = Evaluation
    form_class = AssessmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=AssessmentForm):
        form = super().get_form(form_class)
        form.helper = AssessmentFormLayout()
        return form

    def form_valid(self, form):
        if form.is_valid():
            form.instance.field_trial_id = self.kwargs["field_trial_id"]
            assessment = form.instance
            assessment.save()
            return HttpResponseRedirect(
                self.get_success_url(
                    assessment.field_trial.id))

    def get_success_url(self, field_trial_id):
        return reverse(
            'assessment-list',
            kwargs={'field_trial_id': field_trial_id})


class AssessmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Evaluation
    form_class = AssessmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=AssessmentForm):
        form = super().get_form(form_class)
        form.helper = AssessmentFormLayout(new=False)
        return form


class AssessmentDeleteView(DeleteView):
    model = Evaluation
    template_name = 'trialapp/assessment_delete.html'
    _field_trial_id = None

    def delete(self, *args, **kwargs):
        self.object = self.get_object()
        self._field_trial_id = self.object.field_trial_id
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'assessment-list',
            kwargs={'field_trial_id': self._field_trial_id})


class AssessmentApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/assessment_show.html'
        evaluation_id = kwargs.get('evaluation_id', None)
        dataHelper = DataHelper(evaluation_id)
        dataEvaluation = dataHelper.showDataEvaluation()
        return render(request, template_name, dataEvaluation)
