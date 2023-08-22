from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from trialapp.models import FieldTrial, Thesis, Application
from trialapp.trial_helper import LayoutTrial, TrialModel, TrialPermission
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from baaswebapp.models import Weather
from trialapp.data_models import ReplicaData, Assessment
from baaswebapp.graphs import GraphTrial, WeatherGraphFactory
from trialapp.data_views import DataGraphFactory


class TrialApi(LoginRequiredMixin, DetailView):
    model = FieldTrial
    template_name = 'trialapp/trial_show.html'
    context_object_name = 'trial'

    def whatGraphToShow(self):
        return ['weather', 'efficacy', 'evaluation']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trial = self.get_object()
        # Add additional data to the context
        trialPermision = TrialPermission(trial,
                                         self.request.user).getPermisions()
        allThesis, thesisDisplay = Thesis.getObjectsDisplay(trial)
        assessments = Assessment.getObjects(trial)

        dataTrial = TrialModel.prepareDataItems(trial)
        for item in assessments:
            dataTrial['Assessments'].append(
                {'value': item.getContext(), 'name': item.assessment_date,
                 'link': 'assessment', 'id': item.id})
        other_trials = FieldTrial.objects.filter(product=trial.product).count()
        showData = {
            'description': trial.getDescription(),
            'location': trial.getLocation(),
            'period': trial.getPeriod(),
            'efficacy': '?',
            'other_trials': other_trials,
            'dataTrial': dataTrial, 'thesisList': thesisDisplay,
            'numberAssessments': len(assessments),
            'graphInfo': self.whatGraphToShow(),
            'numberThesis': len(allThesis)}

        if trial.trial_meta == FieldTrial.TrialMeta.FIELD_TRIAL:
            for item in Application.getObjects(trial):
                dataTrial['Applications'].append(
                    {'name': item.getName(), 'value': item.app_date})
            showData['rowsReplicaHeader'] = LayoutTrial.headerLayout(
                trial)
            showData['rowsReplicas'] = LayoutTrial.showLayout(trial,
                                                              None,
                                                              allThesis)
        return {**context, **showData, **trialPermision}


class TrialContent():
    _trial = None
    _content = None
    _request = None

    def __init__(self, request):
        self._request = request
        id = int(request.GET.get('id', 0))
        self._trial = get_object_or_404(FieldTrial, pk=id)
        self._content = request.GET.get('content_type')

    def getGraphData(self, level, rateSets, ratedParts):
        graphs = []
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
                    graphF = DataGraphFactory(level, assmts, dataPoints,
                                              references=self._thesis)
                    graphs.append({'title': graphF.getTitle(),
                                   'content': graphF.draw()})

        return graphs

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

        return WeatherGraphFactory.build(
            dates, non_recent_dates, mean_temps, min_temps,
            max_temps, precip, precip_hrs, soil_moist_1,
            soil_moist_2, soil_moist_3, soil_moist_4,
            soil_temps_1, soil_temps_2, soil_temps_3,
            soil_temps_4, rel_humid, dew_point)

    def fetch(self):
        content = [{'title': self._content,
                    'content': f"<p>Content for {self._trial.name}</p>"}]
        if self._content == 'weather':
            weatherData = self.getWeatherData()
            weatherGraphs = self.graphWeatherData(weatherData)
            content = [{'title': item,
                        'content': weatherGraphs[item]}
                       for item in weatherGraphs]
        elif self._content == 'evaluation':
            self._thesis = Thesis.getObjects(self._trial, as_dict=True)
            new_list = Assessment.getObjects(self._trial)
            rateSets = Assessment.getRateSets(new_list)
            ratedParts = Assessment.getRatedParts(new_list)
            content = self.getGraphData(
                GraphTrial.L_REPLICA, rateSets, ratedParts)
        return render(self._request,
                      'trialapp/trial_content.html',
                      {'dataContent': content})


@login_required
def trialContentApi(request):
    return TrialContent(request).fetch()
