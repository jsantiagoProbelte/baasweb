# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from baaswebapp.models import RateTypeUnit
from trialapp.models import FieldTrial
from trialapp.data_models import ThesisData, ReplicaData, SampleData,\
    Assessment
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView

from baaswebapp.graphs import GraphTrial
from trialapp.data_views import DataHelper, DataGraphFactory
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from rest_framework.response import Response
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.forms import MyDateInput

CLASS_DATA_LEVEL = {
        GraphTrial.L_REPLICA: ReplicaData,
        GraphTrial.L_SAMPLE: SampleData,
        GraphTrial.L_THESIS: ThesisData}


class AssessmentListView(LoginRequiredMixin, ListView):
    model = Assessment
    paginate_by = 100  # if pagination is desired
    login_url = '/login'
    template_name = 'trialapp/assessment_list.html'
    _trial = None

    def getGraphData(self, level, rateSets, ratedParts, columns=2):
        graphs = []
        rowGraphs = []
        foundData = 0
        for rateSet in rateSets:
            for ratedPart in ratedParts:
                classDataModel = CLASS_DATA_LEVEL[level]
                assVIds = Assessment.objects.filter(
                    field_trial_id=self._trial.id,
                    part_rated=ratedPart,
                    rate_type=rateSet).values('id')
                assIds = [value['id'] for value in assVIds]
                dataPoints = classDataModel.getAssessmentDataPoints(assIds)
                if len(dataPoints):
                    foundData += 1
                    graph = DataGraphFactory(level, rateSet, ratedPart,
                                             dataPoints)
                    if len(rowGraphs) == columns:
                        graphs.append(rowGraphs)
                        rowGraphs = []
                    rowGraphs.append(graph.draw())
        if len(rowGraphs) > 0:
            graphs.append(rowGraphs)
        classGraph = GraphTrial.classColGraphs(foundData, columns)
        return graphs, classGraph

    def get_context_data(self, **kwargs):
        field_trial_id = None
        # from call on server
        field_trial_id = self.kwargs['field_trial_id']
        self._trial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Assessment.getObjects(self._trial)
        rateSets = Assessment.getRateSets(new_list)
        ratedParts = Assessment.getRatedParts(new_list)

        # Replica data
        graphPlotsR, classGraphR = self.getGraphData(
            GraphTrial.L_REPLICA, rateSets, ratedParts)

        # Thesis data
        graphPlotsT, classGraphT = self.getGraphData(
            GraphTrial.L_THESIS, rateSets, ratedParts)

        show_active_replica = 'show active'
        show_active_thesis = ''
        active_replica = 'active'
        active_thesis = ''
        if len(graphPlotsT) > 0:
            show_active_thesis = 'show active'
            show_active_replica = ''
            active_replica = ''
            active_thesis = 'active'

        # Sample data
        graphPlotsS, classGraphS = self.getGraphData(
            GraphTrial.L_SAMPLE, rateSets, ratedParts)

        return {'object_list': new_list,
                'fieldTrial': self._trial,
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
                Field('assessment_date', css_class='mb-3'),
                Field('crop_stage_majority', css_class='mb-3'),
                Field('rate_type', css_class='mb-3'),
                Field('part_rated', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")
            ))


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ('name', 'crop_stage_majority', 'assessment_date',
                  'rate_type', 'part_rated')

    def __init__(self, *args, **kwargs):
        super(AssessmentForm, self).__init__(*args, **kwargs)
        self.fields['assessment_date'].widget = MyDateInput()
        self.fields['crop_stage_majority'].label = 'Crop Stage Majority (BBCH)'
        self.fields['rate_type'].queryset =\
            RateTypeUnit.objects.all().order_by('name', 'unit')
        self.fields['part_rated'].required = False


class AssessmentCreateView(LoginRequiredMixin, CreateView):
    model = Assessment
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
            Assessment.computeDDT(assessment.field_trial)
            return HttpResponseRedirect(assessment.get_success_url())


class AssessmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=AssessmentForm):
        form = super().get_form(form_class)
        form.helper = AssessmentFormLayout(new=False)
        return form

    def form_valid(self, form):
        if form.is_valid():
            assessment = form.instance
            assessment.save()
            Assessment.computeDDT(assessment.field_trial)
            return HttpResponseRedirect(assessment.get_success_url())


class AssessmentDeleteView(DeleteView):
    model = Assessment
    template_name = 'trialapp/assessment_delete.html'
    _trial = None

    def get_success_url(self):
        if self._trial is None:
            return '/fieldtrials/'
        else:
            return reverse(
                'assessment-list',
                kwargs={'field_trial_id': self._trial.id})

    def form_valid(self, form):
        self._trial = self.object.field_trial
        respose = super().form_valid(form)
        Assessment.computeDDT(self._trial)
        return respose


class AssessmentApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        template_name = 'trialapp/assessment_show.html'
        assessment_id = kwargs.get('assessment_id', None)
        dataHelper = DataHelper(assessment_id)
        dataAssessment = dataHelper.showDataAssessment()
        return render(request, template_name, dataAssessment)

    # see generateDataPointId
    def post(self, request, format=None):
        # noqa:                      2              1
        # noqa: E501 data_point_id-[level]-[pointId]
        theIds = request.POST['data_point_id'].split('-')
        assId = theIds[-1]
        ass = Assessment.objects.get(id=assId)

        if 'rate_type' in request.POST:
            ass.rate_type_id = int(request.POST['rate_type'])
        elif 'name' in request.POST:
            ass.name = request.POST['name']
        elif 'assessment_date' in request.POST:
            ass.assessment_date = request.POST['assessment_date']
        elif 'part_rated' in request.POST:
            ass.part_rated = request.POST['part_rated']
        elif 'crop_stage_majority' in request.POST:
            ass.crop_stage_majority = request.POST['crop_stage_majority']
        ass.save()
        return Response({'success': True})
