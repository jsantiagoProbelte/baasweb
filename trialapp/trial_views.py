from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from trialapp.models import FieldTrial, Thesis, Application, TreatmentThesis
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
from trialapp.trial_analytics import Abbott
from catalogue.models import UNTREATED


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
    _assmts = None
    _thesis = None

    WEATHER = 'weather_graphs'
    WEATHER_AVG = 'weather_avg'
    ASSESSMENTS = 'assess_graphs'
    RESULT_SUMMARY = 'result_summary'
    KEY_ASSESS = 'key_assess'

    def __init__(self, trialId, content):
        self._trial = get_object_or_404(FieldTrial, pk=trialId)
        self._content = content
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

    def getAssGraphData(self, rateSets, ratedParts,
                        type_graph, showEfficacy=False,
                        xAxis=GraphTrial.L_DATE,
                        level=GraphTrial.L_REPLICA):
        graphs = []
        for rateSet in rateSets:
            for ratedPart in ratedParts:
                assmts = Assessment.objects.filter(
                    field_trial_id=self._trial.id,
                    part_rated=ratedPart,
                    rate_type=rateSet).order_by(
                        'assessment_date')
                assIds = [value.id for value in assmts]

                if level != GraphTrial.L_REPLICA:
                    continue
                dataPoints = ReplicaData.dataPointsAssessAvg(assIds)

                if not dataPoints:
                    continue

                if showEfficacy:
                    orderAssmts = self.getOrderAssmts(assmts)
                    dataPoints = self.calculateDataPointsEfficacy(
                        dataPoints, orderAssmts)

                graphF = DataGraphFactory(
                    level, assmts, dataPoints, showTitle=False,
                    xAxis=xAxis, references=self._thesis)
                if type_graph == GraphTrial.LINE and len(assmts) == 1:
                    type_graph = GraphTrial.COLUMN
                graphs.append(
                    {'title': graphF.getTitle(),
                     'extra_title': _('efficacy'),
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
            return self.graphWeatherData(weatherData)
        else:
            return [
                {'title': _("weather conditions"),
                 'content': _("Weather conditions cannot be determined "
                              "because location or assessments info are"
                              "missing")}]

    def fetchWeatherAvg(self):
        temp_avg = '??'
        hum_avg = '??'
        prep_avg = '??'
        avgData = Weather.objects.filter(
            date__range=(self._min_date, self._max_date),
            latitude=self._trial.latitude,
            longitude=self._trial.longitude
        ).aggregate(
                temp_avg=Avg('mean_temp'),
                prep_avg=Avg('precipitation'),
                hum_avg=Avg('relative_humidity'))
        if avgData['temp_avg']:
            temp_avg = round(avgData['temp_avg'], 0)
            prep_avg = round(avgData['prep_avg'], 0)
            hum_avg = round(avgData['hum_avg'], 0)
        return {'temp_avg': temp_avg, 'hum_avg': hum_avg, 'prep_avg': prep_avg}

    def getRateTupeUnitsAndParts(self):
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        ass_list = Assessment.getObjects(self._trial)
        rateSets = Assessment.getRateSets(ass_list)
        ratedParts = Assessment.getRatedParts(ass_list)
        return rateSets, ratedParts

    def fetchAssessmentsData(self):
        rateSets, ratedParts = self.getRateTupeUnitsAndParts()
        return self.getAssGraphData(
            rateSets, ratedParts, GraphTrial.LINE, showEfficacy=False,
            xAxis=GraphTrial.L_DATE)

    def fetchResultSummaryData(self):
        rateSets, ratedParts = self.getRateTupeUnitsAndParts()
        return self.getAssGraphData(
            rateSets, ratedParts, GraphTrial.COLUMN, showEfficacy=True,
            xAxis=GraphTrial.L_ASSMT)

    def fetchKeyAssessData(self):
        content = self.getKeyGraphData()

        if content:
            return content
        else:
            error = _("Efficacy cannot be determined yet."
                      "Data is not available,"
                      "key thesis or untreated thesis are not well identified,"
                      "key rate type unit is not well identified.")
            return {'error': error}

    def fetchDefault(self):
        return [{'title': self._content,
                 'content': f"<p>Content for {self._trial.name}</p>"}]

    def getAssmts(self, force=False):
        if self._assmts is None or force:
            self._assmts = Assessment.getObjects(self._trial)
        return self._assmts

    def getThesis(self):
        if self._thesis is None:
            self._thesis = Thesis.getObjects(self._trial)
        return self._thesis

    def whatIsKeyRates(self, force=False):
        # Trial should have designated a key part rated
        if not self._trial.key_ratedpart or \
           not self._trial.key_ratetypeunit or \
           force:
            # if key rateset is not designated yet, we nomine one
            counts = {}
            for ass in self.getAssmts():
                combo = f"{ass.rate_type.id} - {ass.part_rated}"

                if combo not in counts:
                    counts[combo] = {'part': ass.part_rated,
                                     'type': ass.rate_type,
                                     'count': 0}
                counts[combo]['count'] += 1
            cmax = 0
            best = None
            for combo in counts:
                if cmax < counts[combo]['count']:
                    cmax = counts[combo]['count']
                    best = combo

            if best:
                self._trial.key_ratedpart = counts[best]['part']
                self._trial.key_ratetypeunit = counts[best]['type']
                self._trial.save()
        return self._trial.key_ratetypeunit, self._trial.key_ratedpart

    def whatIsKeyThesis(self, force=False):
        # Trial should have designated a key thesis
        if not self._trial.key_thesis or force:
            # if key_thesis is not designated yet, we nomine one
            # simple idea, pick the first thesis from product key with
            # biggest dosis
            max_rate = 0
            for thesis in self.getThesis():
                treatments = TreatmentThesis.getObjects(thesis)
                for ttreatment in treatments:
                    if ttreatment.treatment.rate > max_rate:
                        product = ttreatment.treatment.batch.product_variant.product  # noqa E501
                        if product.vendor and product.vendor.key_vendor:
                            self._trial.key_thesis = ttreatment.thesis.id
                            self._trial.save()
        return self._trial.key_thesis

    def whatIsControlThesis(self, force=False):
        if not self._trial.untreated_thesis or force:
            # if untreated_thesis is not designated yet, we nomine one
            # simple idea, use the first treatment pointed to the untreated
            for thesis in self.getThesis():
                treatments = TreatmentThesis.getObjects(thesis)
                for ttreatment in treatments:
                    if ttreatment.treatment.batch.product_variant.product.name == UNTREATED: # noqa E501
                        self._trial.untreated_thesis = ttreatment.thesis.id
                        self._trial.save()
                        break
        return self._trial.untreated_thesis

    def whatIsBestEfficacy(self, bestEfficacy, force=False):
        if self._trial.best_efficacy != bestEfficacy and force:
            self._trial.best_efficacy = bestEfficacy
            self._trial.save()
        return self._trial.best_efficacy

    def getKeyAssData(self, keyRateTypeUnit, keyPartRated,
                      keyThesisId, untreatedThesisId):
        if not keyRateTypeUnit or not keyPartRated or\
           not keyThesisId or not untreatedThesisId:
            return None

        dataPoints = ReplicaData.dataPointsKeyAssessAvg(
            keyRateTypeUnit, keyPartRated,
            keyThesisId, untreatedThesisId)

        if len(dataPoints) > 1:
            return dataPoints
        else:
            return None

    def getKeyAssmts(self, keyRateTypeUnit, keyPartRated):
        return Assessment.objects.filter(
            rate_type_id=keyRateTypeUnit.id,
            part_rated=keyPartRated)

    def getKeyGraphData(self):
        keyRateTypeUnit, keyPartRated = self.whatIsKeyRates()
        keyThesisId = self.whatIsKeyThesis()
        untreatedThesisId = self.whatIsControlThesis()
        dataPoints = self.getKeyAssData(
            keyRateTypeUnit, keyPartRated, keyThesisId, untreatedThesisId)

        if not dataPoints:
            return None

        assmts = self.getKeyAssmts(keyRateTypeUnit, keyPartRated)
        keyThesis = Thesis.objects.get(id=keyThesisId)
        untreatedThesis = Thesis.objects.get(id=untreatedThesisId)
        bestEfficacy, line = self.calculateBestEfficacy(
            dataPoints, assmts, keyThesisId, untreatedThesisId)
        thesiss = {
            keyThesisId: keyThesis,
            untreatedThesisId: untreatedThesis}
        graphF = DataGraphFactory(
            GraphTrial.L_REPLICA, assmts, dataPoints,
            references=thesiss, showTitle=False)
        num_assmts = len(assmts)
        graphF.addLineColorsToTraces(keyThesis.number,
                                     untreatedThesis.number)
        if num_assmts > 1:
            graphF.addTrace(line, "best efficacy")
        content = graphF.drawConclusionGraph(num_assmts)
        explanation = self.bestEfficiencyExplanation(
            keyRateTypeUnit, keyPartRated)

        if bestEfficacy:
            self.whatIsBestEfficacy(bestEfficacy, force=True)
        return {'conclusion_graph': content,
                'key_treatment_product': keyThesis.getKeyProduct(),
                'unit_name': keyRateTypeUnit.getName(),
                'bestEfficiencyExplanation': explanation,
                # see return on calculateBestEfficacy
                'control_value': line['y'][0],
                'best_keytesis_value': line['y'][1],
                'bestEfficacy': bestEfficacy}

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

    def getOrderAssmts(self, assmts):
        # This assmts are retrieved in order by date
        orderAss = {}
        order = 1
        for assmt in assmts:
            orderAss[assmt.id] = order
            order += 1
        return orderAss

    def calculateDataPointsEfficacy(self, dataPoints, orderAssmts):
        controlThesisId = self.whatIsControlThesis()
        if not controlThesisId:
            return None
        values = {}
        for point in dataPoints:
            assId = point['assessment__id']
            if assId not in values:
                values[assId] = {}
            thesisId = point['reference__thesis__id']
            values[assId][thesisId] = point['value']

        efficacies = []
        for assId in values:
            assValues = values[assId]
            controlValue = assValues[controlThesisId]
            for thesisId in assValues:
                if thesisId == controlThesisId:
                    continue
                efficacies.append({
                    'assessment__id': assId,
                    'assessment__number': orderAssmts[assId],
                    'reference__thesis__id': thesisId,
                    'value': self.calculateEfficacy(controlValue,
                                                    assValues[thesisId])})
        return efficacies

    def bestEfficiencyExplanation(self, keyRateTypeUnit, keyPartRated):
        explanation = _('* in the moment of maximum difference at ')
        explanation += keyRateTypeUnit.getName()
        if keyPartRated is not None and keyPartRated != 'Undefined':
            explanation += _(" in ")
            explanation += keyPartRated
        return explanation

    FETCH_FUNCTIONS = {
        WEATHER: fetchWeather,
        KEY_ASSESS: fetchKeyAssessData,
        ASSESSMENTS: fetchAssessmentsData,
        WEATHER_AVG: fetchWeatherAvg,
        RESULT_SUMMARY: fetchResultSummaryData}

    TEMPLATE_CARDS = 'trialapp/trial_content_cards.html'
    TEMPLATE_DIVS = 'trialapp/trial_content_divs.html'
    TEMPLATE_CONCLUSION_GRAPH = 'trialapp/trial_conclusion_graph.html'

    FETCH_TEMPLATES = {
        WEATHER: TEMPLATE_CARDS,
        KEY_ASSESS: TEMPLATE_CONCLUSION_GRAPH,
        ASSESSMENTS: TEMPLATE_CARDS,
        WEATHER_AVG: 'trialapp/trial_weather_avg.html',
        RESULT_SUMMARY: TEMPLATE_CARDS}

    def fetch(self):
        theFetch = TrialContent.FETCH_FUNCTIONS.get(
            self._content, TrialContent.fetchDefault)
        content = theFetch(self)
        template = TrialContent.FETCH_TEMPLATES.get(
            self._content, TrialContent.TEMPLATE_CARDS)
        return render(self._request, template, {'dataContent': content})


@login_required
def trialContentApi(request):
    trialId = int(request.GET.get('id', 0))
    content = request.GET.get('content_type')
    return TrialContent(trialId, content).fetch()
