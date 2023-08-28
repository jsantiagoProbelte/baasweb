from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from trialapp.models import FieldTrial, Thesis, Application
from trialapp.trial_helper import LayoutTrial, TrialModel, TrialPermission
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from baaswebapp.models import Weather, Category
from trialapp.data_models import ReplicaData, Assessment
from baaswebapp.graphs import GraphTrial, WeatherGraphFactory
from trialapp.data_views import DataGraphFactory
from django.db.models import Min, Max
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from trialapp.trial_helper import TrialHelper
from trialapp.trial_analytics import Abbott


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
        control_product = False
        if trial.product.category() == Category.CONTROL:
            control_product = True
        showData = {
            'description': trial.getDescription(),
            'location': trial.getLocation(),
            'period': trial.getPeriod(),
            'efficacy': trial.best_efficacy if trial.best_efficacy else '?',
            'other_trials': other_trials,
            'control_product': control_product,
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
    _category = None

    WEATHER = 'weather'
    ASSESSMENTS = 'ass'
    EFFICACY = 'eff'
    KEY_ASSESS = 'key_assess'

    def __init__(self, request):
        self._request = request
        id = int(request.GET.get('id', 0))
        self._trial = get_object_or_404(FieldTrial, pk=id)
        self._content = request.GET.get('content_type')
        self._category = self._trial.product.category()
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
                    dataPoints = ReplicaData.dataPointsAssessAvg(assIds)
                else:
                    dataPoints = []
                if len(dataPoints):
                    graphF = DataGraphFactory(level, assmts, dataPoints,
                                              showTitle=False,
                                              references=self._thesis)
                    type_graph = GraphTrial.LINE if len(assmts) > 1\
                        else GraphTrial.COLUMN
                    graphs.append(
                        {'title': graphF.getTitle(),
                         'content': graphF.draw(type_graph=type_graph)})
        return graphs

    def calculateEfficacy(self, controlValue, keyThesisValue):
        if self._category == Category.CONTROL:
            return abs(Abbott.do(keyThesisValue, controlValue))
        else:
            eff = (keyThesisValue - controlValue) / controlValue
            return round((eff*100)+100, 2)

    def calculateBestEfficacy(self, dataPoints, assmts,
                              keyThesisId, untreatedThesisId):
        bestEfficacy = 0
        dateMaxDistance = None
        pointU = None
        pointK = None
        values = {}
        assmtsDates = {assm.id: assm.assessment_date for assm in assmts}
        for point in dataPoints:
            ddate = assmtsDates[point['assessment__id']]
            thesisId = point['reference__thesis__id']
            if ddate not in values:
                values[ddate] = {}
            if thesisId == keyThesisId:
                values[ddate]['k'] = point['value']
            if thesisId == untreatedThesisId:
                values[ddate]['u'] = point['value']
        for ddate in values:
            value = values[ddate]
            if 'k' not in value or 'u' not in value:
                continue
            thisEfficacy = self.calculateEfficacy(value['u'], value['k'])
            if thisEfficacy > bestEfficacy:
                bestEfficacy = thisEfficacy
                dateMaxDistance = ddate
                pointU = value['u']
                pointK = value['k']

        if bestEfficacy > 0:
            lines = {'y': [round(pointU, 2), round(pointK, 2)],
                     'x': [dateMaxDistance, dateMaxDistance]}
            return bestEfficacy, lines
        else:
            return None, None

    def bestEfficiencyExplanation(self, keyRateTypeUnit, keyPartRated):
        explanation = _('* in the moment of maximum difference at ')
        explanation += keyRateTypeUnit.getName()
        if keyPartRated is not None and keyPartRated != 'Undefined':
            explanation += _(" in ")
            explanation += keyPartRated
        return explanation

    def getKeyGraphData(self, keyRateTypeUnit,
                        keyPartRated,
                        keyThesisId,
                        untreatedThesisId):
        dataPoints = []

        if keyRateTypeUnit and keyPartRated and\
           keyThesisId and untreatedThesisId:
            dataPoints = ReplicaData.dataPointsKeyAssessAvg(
                keyRateTypeUnit, keyPartRated,
                keyThesisId, untreatedThesisId)

        if len(dataPoints):
            assmts = Assessment.objects.filter(
                rate_type_id=keyRateTypeUnit.id,
                part_rated=keyPartRated)
            keyThesis = Thesis.objects.get(id=keyThesisId)
            untreatedThesis = Thesis.objects.get(id=untreatedThesisId)
            bestEfficacy, line = self.calculateBestEfficacy(
                dataPoints, assmts, keyThesisId, untreatedThesisId)
            thesis = {
                keyThesisId: keyThesis,
                untreatedThesisId: untreatedThesis}
            graphF = DataGraphFactory(
                GraphTrial.L_REPLICA, assmts, dataPoints,
                references=thesis, showTitle=False)
            num_assmts = len(assmts)
            graphF.addLineColorsToTraces(keyThesis.number,
                                         untreatedThesis.number)
            if num_assmts > 1:
                graphF.addTrace(line, "best efficacy")
            content = graphF.drawConclusionGraph(num_assmts)
            explanation = self.bestEfficiencyExplanation(
                keyRateTypeUnit, keyPartRated)
            return {'conclusion_graph': content,
                    'key_treatment_product': keyThesis.getKeyProduct(),
                    'unit_name': keyRateTypeUnit.getName(),
                    'bestEfficiencyExplanation': explanation,
                    # see return on calculateBestEfficacy
                    'control_value': line['y'][0],
                    'best_keytesis_value': line['y'][1],
                    'bestEfficacy': bestEfficacy}
        else:
            error = _("Efficacy cannot be determined yet."
                      "Data is not available,"
                      "key thesis or untreated thesis are not well identified,"
                      "key rate type unit is not well identified.")
            return {'error': error}

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
            return self.graphWeatherData(weatherData)
        else:
            return [
                {'title': _("weather conditions"),
                 'content': _("Weather conditions cannot be determined "
                              "because location or assessments info are"
                              "missing")}]

    def fetchAssessmentsData(self):
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        ass_list = Assessment.getObjects(self._trial)
        rateSets = Assessment.getRateSets(ass_list)
        ratedParts = Assessment.getRatedParts(ass_list)
        return self.getGraphData(GraphTrial.L_REPLICA, rateSets, ratedParts)

    def fetchKeyAssessData(self):
        tHelper = TrialHelper(self._trial)
        keyRateTypeUnit, keyPartRated = tHelper.whatIsKeyRates()
        keyThesis = tHelper.whatIsKeyThesis()
        untreatedThesis = tHelper.whatIsControlThesis()

        # Choose the rate_unit with most data.
        keyData = self.getKeyGraphData(keyRateTypeUnit,
                                       keyPartRated,
                                       keyThesis,
                                       untreatedThesis)
        if 'bestEfficacy' in keyData:
            tHelper.whatIsBestEfficacy(keyData['bestEfficacy'])
        return keyData

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

    TEMPLATE_CARDS = 'trialapp/trial_content_cards.html'
    TEMPLATE_DIVS = 'trialapp/trial_content_divs.html'
    TEMPLATE_CONCLUSION_GRAPH = 'trialapp/trial_conclusion_graph.html'

    FETCH_TEMPLATES = {
        WEATHER: TEMPLATE_CARDS,
        KEY_ASSESS: TEMPLATE_CONCLUSION_GRAPH,
        ASSESSMENTS: TEMPLATE_CARDS,
        EFFICACY: TEMPLATE_CARDS}

    def fetch(self):
        theFetch = TrialContent.FETCH_FUNCTIONS.get(
            self._content, TrialContent.fetchDefault)
        content = theFetch(self)
        template = TrialContent.FETCH_TEMPLATES.get(
            self._content, TrialContent.TEMPLATE_CARDS)
        return render(self._request, template, {'dataContent': content})


@login_required
def trialContentApi(request):
    return TrialContent(request).fetch()
