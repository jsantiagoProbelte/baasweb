# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from baaswebapp.models import RateTypeUnit, Weather
from trialapp.models import FieldTrial, Thesis
from trialapp.data_models import ThesisData, ReplicaData, SampleData, \
    Assessment
from django.shortcuts import get_object_or_404
from baaswebapp.graphs import GraphTrial, WeatherGraphFactory
from trialapp.data_views import DataGraphFactory
from django.views.generic import DetailView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from crispy_forms.bootstrap import FormActions
from django.http import HttpResponseRedirect
from django import forms
from trialapp.trial_helper import TrialPermission
from baaswebapp.models import EventBaas, EventLog
from trialapp.trial_views import TrialContent


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
    _thesis = None

    def getGraphData(self, level, rateSets, ratedParts, columns=2):
        graphs = []
        rowGraphs = []
        foundData = 0
        for rateSet in rateSets:
            for ratedPart in ratedParts:
                assmts = Assessment.objects.filter(
                    field_trial_id=self._trial.id,
                    part_rated=ratedPart,
                    rate_type=rateSet)
                assIds = [value.id for value in assmts]

                if level == GraphTrial.L_REPLICA:
                    dataPoints = ReplicaData.dataPointsAssess(assIds)
                else:
                    dataPoints = []
                if len(dataPoints):
                    foundData += 1
                    graph = DataGraphFactory(level, assmts, dataPoints,
                                             references=self._thesis)
                    if len(rowGraphs) == columns:
                        graphs.append(rowGraphs)
                        rowGraphs = []
                    rowGraphs.append(graph.draw())
        if len(rowGraphs) > 0:
            graphs.append(rowGraphs)
        classGraph = GraphTrial.classColGraphs(foundData, columns)
        return graphs, classGraph

    def getWeatherData(self):
        assessments = Assessment.getObjects(self._trial)
        weather_data = []
        weather_assess_dict = {}
        for assessment in assessments:
            weather = Weather.objects.filter(
                date=assessment.assessment_date, latitude=self._trial.latitude,
                longitude=self._trial.longitude)
            if weather:
                weather_data.append(weather.first())
                weather_assess_dict[assessment.id] = weather.first()
        return weather_data, weather_assess_dict

    def graphWeatherData(self, weather_data):
        dates = [o.date for o in weather_data]
        non_recent_dates = [o.date for o in weather_data if not o.recent]
        min_temps = [o.min_temp for o in weather_data]
        max_temps = [o.max_temp for o in weather_data]
        mean_temps = [o.mean_temp for o in weather_data]
        precip = [o.precipitation for o in weather_data]
        precip_hrs = [o.precipitation_hours for o in weather_data]
        soil_temps_1 = [o.soil_temp_0_to_7cm for o in weather_data]
        soil_temps_2 = [o.soil_temp_7_to_28cm for o in weather_data]
        soil_temps_3 = [o.soil_temp_28_to_100cm for o in weather_data]
        soil_temps_4 = [o.soil_temp_100_to_255cm for o in weather_data]
        soil_moist_1 = [o.soil_moist_0_to_7cm for o in weather_data]
        soil_moist_2 = [o.soil_moist_7_to_28cm for o in weather_data]
        soil_moist_3 = [o.soil_moist_28_to_100cm for o in weather_data]
        soil_moist_4 = [o.soil_moist_100_to_255cm for o in weather_data]
        dew_point = [o.dew_point for o in weather_data]
        rel_humid = [o.relative_humidity for o in weather_data]

        return WeatherGraphFactory.build(
            dates, non_recent_dates, mean_temps, min_temps,
            max_temps, precip, precip_hrs, soil_moist_1,
            soil_moist_2, soil_moist_3, soil_moist_4,
            soil_temps_1, soil_temps_2, soil_temps_3,
            soil_temps_4, rel_humid, dew_point)

    def get_context_data(self, **kwargs):
        field_trial_id = None
        # from call on server
        field_trial_id = self.kwargs['field_trial_id']
        self._trial = get_object_or_404(FieldTrial, pk=field_trial_id)
        new_list = Assessment.getObjects(self._trial)
        rateSets = Assessment.getRateSets(new_list)
        ratedParts = Assessment.getRatedParts(new_list)
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        hasThesis = len(list(Thesis.getObjects(self._trial))) > 0

        # Replica data
        graphPlotsR, classGraphR = self.getGraphData(
            GraphTrial.L_REPLICA, rateSets, ratedParts)

        # Thesis data
        graphPlotsT, classGraphT = self.getGraphData(
            GraphTrial.L_THESIS, rateSets, ratedParts)

        # TODO: Sample data
        # graphPlotsS, classGraphS = self.getGraphData(
        #     GraphTrial.L_SAMPLE, rateSets, ratedParts)
        (weatherData, weather_assess) = self.getWeatherData()
        try:
            new_list = list(map(lambda ass: {
                'assessment_date': ass.assessment_date,
                'part_rated': ass.part_rated,
                'crop_stage_majority': ass.crop_stage_majority,
                'rate_type': ass.rate_type,
                'temp_avg': int(weather_assess[ass.id].mean_temp) if weather_assess.get(ass.id, None) else None,
                'hum_avg': int(weather_assess[ass.id].relative_humidity) if weather_assess.get(ass.id, None) else None,
                'prep_avg': f"{ int(weather_assess[ass.id].precipitation) }" if weather_assess.get(ass.id, None) else None,
                'id': ass.id,
                'hasWeather': weather_assess.get(ass.id, None),
                'name': ass.name,
                'unit': ass.unit,
                'part_rated_unit': ass.part_rated_unit
                }, new_list))
        except Exception as error:
            print(error)
        weatherGraph = self.graphWeatherData(weatherData)
        permisions = TrialPermission(
            self._trial, self.request.user).getPermisions()
        return {'object_list': new_list,
                'title': f"({len(new_list)}) Assessments",
                'fieldTrial': self._trial,
                'graphPlotsR': graphPlotsR, 'classGraphR': classGraphR,
                'graphPlotsT': graphPlotsT, 'classGraphT': classGraphT,
                'weatherGraph': weatherGraph, 'hasThesis': hasThesis,
                **permisions}


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
                Field('unit', css_class='mb-3'),
                Field('part_rated_unit', css_class='mb-3'),
                FormActions(
                    Submit('submit', submitTxt, css_class="btn btn-info"),
                    css_class='text-sm-end'),
                css_class="card-body-baas mt-2")))


class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ('name', 'crop_stage_majority', 'assessment_date',
                  'rate_type', 'part_rated', 'unit', 'part_rated_unit')

    def __init__(self, *args, **kwargs):
        super(AssessmentForm, self).__init__(*args, **kwargs)
        self.fields['assessment_date'].widget = forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control',
                   'type': 'date'})
        self.fields['assessment_date'].show_hidden_initial = True
        self.fields['crop_stage_majority'].label = 'Crop Stage Majority (BBCH)'
        self.fields['rate_type'].queryset =\
            RateTypeUnit.objects.all().order_by('-display_order', 'name')
        self.fields['part_rated'].required = False
        self.fields['unit'].required = False
        self.fields['part_rated_unit'].required = False


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
            EventLog.track(
                EventBaas.NEW_ASS,
                self.request.user.id,
                assessment.field_trial_id)
            return HttpResponseRedirect(assessment.get_absolute_url())


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
            EventLog.track(
                EventBaas.UPDATE_ASS,
                self.request.user.id,
                assessment.field_trial_id)
            Assessment.computeDDT(assessment.field_trial)
            return HttpResponseRedirect(assessment.get_absolute_url())


class AssessmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Assessment
    template_name = 'trialapp/assessment_delete.html'

    def get_success_url(self):
        return reverse(
            'assessment-list',
            kwargs={'field_trial_id': self.get_object().field_trial_id})

    def form_valid(self, form):
        trial = self.get_object().field_trial
        Assessment.computeDDT(trial)
        EventLog.track(
                EventBaas.DELETE_APP,
                self.request.user.id,
                trial.id)
        return super().form_valid(form)


class AssessmentApi(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

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
        EventLog.track(
                EventBaas.UPDATE_ASS,
                0,  # TODO request.user.id if request.user.id else 0,
                ass.field_trial_id)
        return Response({'success': True})


class AssessmentView(LoginRequiredMixin, DetailView):
    model = Assessment
    template_name = 'trialapp/assessment_show.html'
    context_object_name = 'assessment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assessment = self.get_object()
        trialContent = TrialContent(assessment.field_trial_id,
                                    TrialContent.ASSESSMENT_VIEW,
                                    self.request.user,
                                    trial=assessment.field_trial,
                                    extra_id=assessment.id)
        permisions = TrialPermission(
            assessment.field_trial, self.request.user).getPermisions()

        return {'title': assessment.getTitle(),
                **context,
                'fieldTrial': assessment.field_trial,
                'dataContent': trialContent.fetchAssessment(),
                **permisions}
