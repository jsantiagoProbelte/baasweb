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
from django.db.models import Min, Max
from datetime import timedelta
from django.utils.translation import gettext_lazy as _


class TrialApi(LoginRequiredMixin, DetailView):
    model = FieldTrial
    template_name = 'trialapp/trial_show.html'
    context_object_name = 'trial'

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
            'type_product': trial.product.nameType(),
            'dataTrial': dataTrial, 'thesisList': thesisDisplay,
            'numberAssessments': len(assessments),
            'graphInfo': [TrialContent.WEATHER, TrialContent.ASSESSMENTS],
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

    WEATHER = 'weather'
    ASSESSMENTS = 'ass'
    EFFICACY = 'eff'
    KEY_ASSESS = 'key_assess'

    def __init__(self, request):
        self._request = request
        id = int(request.GET.get('id', 0))
        self._trial = get_object_or_404(FieldTrial, pk=id)
        self._content = request.GET.get('content_type')
        assessments = Assessment.getObjects(self._trial)
        if assessments:
            oneweek = timedelta(days=7)
            self._min_date = assessments.aggregate(
                min_date=Min('assessment_date'))['min_date']
            self._min_date -= oneweek
            self._max_date = assessments.aggregate(
                max_date=Max('assessment_date'))['max_date']
            self._max_date += oneweek
        else:
            self._min_date = None
            self._max_date = None

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
                    # dataPoints = ReplicaData.dataPointsAssess(assIds)
                    dataPoints = ReplicaData.dataPointsAssessAvg(assIds)
                else:
                    dataPoints = []
                if len(dataPoints):
                    graphF = DataGraphFactory(level, assmts, dataPoints,
                                              references=self._thesis)
                    type_graph = DataGraphFactory.LINE if len(assmts) > 1\
                        else DataGraphFactory.COLUMN
                    graphs.append(
                        {'title': graphF.getTitle(),
                         'content': graphF.draw(type_graph=type_graph)})
        return graphs

    def getWeatherData(self):
        Weather.enrich(self._min_date, self._max_date,
                       self._trial.latitude,
                       self._trial.longitude)
        return Weather.objects.filter(
            date__range=(self._min_date, self._max_date),
            latitude=self._trial.latitude,
            longitude=self._trial.longitude).order_by('date')

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

    def fetchWeather(self):
        weatherData = self.getWeatherData()
        if weatherData:
            weatherGraphs = self.graphWeatherData(weatherData)
            return [{'title': item,
                    'content': weatherGraphs[item]}
                    for item in weatherGraphs]
        else:
            return [
                {'title': _("weather conditions"),
                 'content': _("Weather conditions cannot be determined "
                              "because location or assessments info are"
                              " missing")}]

    def fetchAssessmentsData(self):
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        ass_list = Assessment.getObjects(self._trial)
        rateSetsCounts = Assessment.getRateSets(ass_list)
        rateSets = list(rateSetsCounts.keys())
        ratedPartCounts = Assessment.getRatedParts(ass_list)
        ratedParts = list(ratedPartCounts.keys())
        return self.getGraphData(GraphTrial.L_REPLICA, rateSets, ratedParts)

    def mostPopular(self, counters):
        if counters and len(counters) > 0:
            if len(counters) == 1:
                return list(counters.keys())[0]
            counts = list(counters.values())
            maxCount = max(counts)
            # We assume , the biggest amount of assessment is the key info
            # This works when there is none or one
            # If there are multiple ones, then the first is winning
            for aKey in counters:
                if maxCount == counters[aKey]:
                    return aKey
        return None

    def whatIsKeyRateSet(self):
        # Trial should have designated a key rate_set
        # TODO: Use one designated by the admin
        keyrateset = None
        if not keyrateset:
            # if key rateset is not designated yet, we nomine one
            ass_list = Assessment.getObjects(self._trial)
            if ass_list:
                rateSetsCounts = Assessment.getRateSets(ass_list)
                keyrateset = self.mostPopular(rateSetsCounts)
        return keyrateset

    def whatIsKeyPartRated(self):
        # Trial should have designated a key part rated
        # TODO: Use one designated by the admin
        keypartrated = None
        if not keypartrated:
            # if key rateset is not designated yet, we nomine one
            ass_list = Assessment.getObjects(self._trial)
            if ass_list:
                partRatedCounts = Assessment.getRatedParts(ass_list)
                keypartrated = self.mostPopular(partRatedCounts)
        return keypartrated

    def fetchKeyAssessData(self):
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        keyRateSet = self.whatIsKeyRateSet()
        keypartrated = self.whatIsKeyPartRated()

        # Choose the rate_unit with most data.
        return self.getGraphData(GraphTrial.L_REPLICA,
                                 [keyRateSet],
                                 [keypartrated])

    def fetchEfficacy(self):
        return self.fetchDefault()

    def fetchDefault(self):
        return [{'title': self._content,
                 'content': f"<p>Content for {self._trial.name}</p>"}]

    FETCH_FUNCTIONS = {
        WEATHER: fetchWeather,
        KEY_ASSESS: fetchKeyAssessData,
        ASSESSMENTS: fetchAssessmentsData,
        EFFICACY: fetchDefault}

    def fetch(self):
        theFetch = TrialContent.FETCH_FUNCTIONS.get(self._content,
                                                    TrialContent.fetchDefault)
        content = theFetch(self)
        return render(self._request,
                      'trialapp/trial_content.html',
                      {'dataContent': content})


@login_required
def trialContentApi(request):
    return TrialContent(request).fetch()
