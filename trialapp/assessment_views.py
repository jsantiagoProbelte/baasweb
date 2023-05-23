# Create your views here.
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
# from rest_framework import permissions
from baaswebapp.models import RateTypeUnit, Weather
from trialapp.models import FieldTrial
from trialapp.data_models import ThesisData, ReplicaData, SampleData,\
    Assessment
from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView

from baaswebapp.graphs import GraphTrial, WeatherGraph
from trialapp.data_views import DataHelper
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from crispy_forms.helper import FormHelper
from django.urls import reverse
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
                    graph = GraphTrial(level, rateSet, ratedPart, dataPoints)
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
        for assessment in assessments:
            weather = Weather.objects.filter(
                date=assessment.assessment_date, latitude=self._trial.latitude,
                longitude=self._trial.longitude)
            if weather:
                weather_data.append(weather.first())
        return weather_data

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

        graph = WeatherGraph(dates, non_recent_dates, mean_temps, min_temps,
                             max_temps, precip, precip_hrs, soil_moist_1,
                             soil_moist_2, soil_moist_3, soil_moist_4,
                             soil_temps_1, soil_temps_2, soil_temps_3,
                             soil_temps_4, rel_humid, dew_point)
        return (graph.draw_temp(), graph.draw_precip(),
                graph.draw_soil_temp(), graph.draw_soil_moist(),
                graph.draw_humid(), graph.draw_dew())

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
        weatherData = self.getWeatherData()
        tGraph, pGraph, sGraph, mGraph, hGraph, dGraph = self.graphWeatherData(
            weatherData)
        return {'object_list': new_list,
                'fieldTrial': self._trial,
                'show_active_thesis': show_active_thesis,
                'show_active_replica': show_active_replica,
                'active_replica': active_replica,
                'active_thesis': active_thesis,
                'graphPlotsR': graphPlotsR, 'classGraphR': classGraphR,
                'graphPlotsT': graphPlotsT, 'classGraphT': classGraphT,
                'graphPlotsS': graphPlotsS, 'classGraphS': classGraphS,
                'tempGraph': tGraph, 'precipGraph': pGraph,
                'soilTempGraph': sGraph, 'soilMoistGraph': mGraph,
                'humidGraph': hGraph, 'dewPointGraph': dGraph}


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
            RateTypeUnit.objects.all().order_by('name')
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
            return HttpResponseRedirect(assessment.get_absolute_url())


class AssessmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = 'baaswebapp/model_edit_form.html'

    def get_form(self, form_class=AssessmentForm):
        form = super().get_form(form_class)
        form.helper = AssessmentFormLayout(new=False)
        return form


class AssessmentDeleteView(DeleteView):
    model = Assessment
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
        assessment_id = kwargs.get('assessment_id', None)
        dataHelper = DataHelper(assessment_id)
        dataAssessment = dataHelper.showDataAssessment()
        return render(request, template_name, dataAssessment)
