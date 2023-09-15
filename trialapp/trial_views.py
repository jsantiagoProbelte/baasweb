from django.db.models import Avg, F, Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from trialapp.models import FieldTrial, Thesis, Application, TreatmentThesis
from trialapp.trial_helper import LayoutTrial, TrialModel, TrialPermission
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from baaswebapp.models import Weather, Category
from trialapp.data_models import ReplicaData, Assessment
from baaswebapp.graphs import GraphTrial, WeatherGraphFactory
from trialapp.data_views import DataGraphFactory
from django.db.models import Min, Max
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from trialapp.trial_analytics import Abbott
from catalogue.models import UNTREATED
from rest_framework.views import APIView
from trialapp.data_views import DataHelper, DataTrialHelper


class TrialApi(LoginRequiredMixin, DetailView):
    model = FieldTrial
    template_name = 'trialapp/trial_show.html'
    context_object_name = 'trial'

    def getSchedule(self, fieldtrial):
        assessments = Assessment.objects.filter(field_trial_id=fieldtrial.id)
        applications = Application.objects.filter(field_trial_id=fieldtrial.id)

        schedule_list = ScheduleAdapter.adapt_list(assessments) + \
            ScheduleAdapter.adapt_list(applications)
        schedule_list.sort(key=lambda schedule_line: schedule_line.date)

        return schedule_list

    def getTrialInfo(self, fieldtrial):
        return FieldTrial.objects.select_related(
                'trial_type',
                'crop',
                'crop__cropvariety'
            ).values(
                'trial_type__name',
                'latitude',
                'longitude',
                'transplant_date',
                'crop__name',
                'crop__scientific',
                'crop__cropvariety__name',
                'crop_age',
                'blocks',
                'distance_between_plants',
                'distance_between_rows',
                'responsible',
                'contact',
                'cro'
            ).filter(
                id=fieldtrial.id
            )[0]

    def getThesisByFieldTrialForDetail(self, fieldtrial):
        bgClass = 'bg-custom-'

        thesisList = Thesis.objects.filter(
            field_trial__id=fieldtrial.id
            ).select_related(
                'field_trial',
                'field_trial__product',
                'field_trial__product__vendor'
            ).values(
                'name',
                'id',
                'field_trial__product__name',
                'field_trial__product__active_substance',
                'field_trial__product__vendor__name'
            ).annotate(
                product_name=F('field_trial__product__name'),
                active_substance=F('field_trial__product__active_substance'),
                vendor_name=F('field_trial__product__vendor__name')
            )
        counter = 1
        thesisWithColor = []
        controlThesis = fieldtrial.control_thesis
        keyThesis = fieldtrial.key_thesis
        for thesis in thesisList:
            idColor = f"{bgClass}{counter}"
            if thesis['id'] == controlThesis:
                idColor = 'bg-custom-control'
            if thesis['id'] == keyThesis:
                idColor = 'bg-custom-key-thesis'
            thesisWithColor.append({'idColor': idColor,
                                    'thesis': thesis})
            counter += 1
        return thesisWithColor

    def getAssesmentsGroupedByPartTreated(self, trial):
        assesments = Assessment.objects.values(
            'part_rated',
            'field_trial_id'
        ).annotate(
            count=Count('id')
        ).filter(field_trial_id=trial.id)

        return assesments

    def getTrialKeyData(self, trial):
        keyThesis = trial.keyThesis()
        keyTreatment = TreatmentThesis.getTreatment(keyThesis)
        dosis = keyTreatment.getDosis() if keyTreatment else None
        return {
            'key_thesis_id': keyThesis.id if keyThesis else None,
            'key_treatment_id': keyTreatment.id if keyTreatment else None,
            'key_dosis_rate': dosis['rate'] if dosis else None,
            'key_dosis_unit': dosis['unit'] if dosis else None,
            'key_interval': keyThesis.interval if keyThesis else None,
            'key_number_apps': keyThesis.number_applications if keyThesis else
            None}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trial = self.get_object()
        # Add additional data to the context
        trialPermision = TrialPermission(trial,
                                         self.request.user)
        tpermisions = trialPermision.getPermisions()
        if not trialPermision.canRead():
            return {**tpermisions,
                    'trial': trial,
                    'description': trial.getDescription,
                    'location': trial.getLocation(),
                    'period': trial.getPeriod(),
                    'error': trialPermision.getError()}

        allThesis, thesisDisplay = Thesis.getObjectsDisplay(trial)
        assessments = Assessment.getObjects(trial)

        dataTrial = TrialModel.prepareDataItems(trial)
        dataTrial['Assessments'] = [
            {'id': item.id, 'name': item.name, 'unit': item.getUnitPartTitle(),
             'date': item.assessment_date}
            for item in assessments]
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
            'trialInfo': self.getTrialInfo(trial),
            'thesisDetail': self.getThesisByFieldTrialForDetail(trial),
            'groupedAssesments': self.getAssesmentsGroupedByPartTreated(trial),
            'numberAssessments': len(assessments),
            'numberThesis': len(allThesis),
            'schedule': self.getSchedule(trial)}

        keyTrialData = self.getTrialKeyData(trial)
        if trial.trial_meta == FieldTrial.TrialMeta.FIELD_TRIAL:
            for item in Application.getObjects(trial):
                dataTrial['Applications'].append(
                    {'name': item.getName(), 'value': item.app_date})
            showData['rowsReplicaHeader'] = LayoutTrial.headerLayout(
                trial)
            showData['rowsReplicas'] = LayoutTrial.showLayout(trial,
                                                              None,
                                                              allThesis)
        return {**context, **showData, **tpermisions, **keyTrialData}


class ScheduleAdapter():
    name = None
    date = None
    previous_type = None
    isAdapted = False

    @staticmethod
    def adapt_list(list):
        adapted_list = []
        for object in list:
            adapted_list.append(ScheduleAdapter(object))

        return adapted_list

    def __init__(self, object):
        self._process_application(object)
        self._process_assesment(object)
        self._check_is_adapted()

    def _process_application(self, application):
        if isinstance(application, Application):
            self.name = application.comment
            self.date = application.app_date
            self.previous_type = 'application'
            self.isAdapted = True

    def _process_assesment(self, assesment):
        if isinstance(assesment, Assessment):
            self.name = assesment.name
            self.date = assesment.assessment_date
            self.previous_type = 'assessment'
            self.isAdapted = True

    def _check_is_adapted(self):
        if not self.isAdapted:
            raise ValueError(
                "The object entered isn't avalaible for Schedule.")


class TrialContent():
    _trial = None
    _content = None
    _request = None
    _category = None
    _assmts = None
    _thesis = None
    _user = None
    _extra_id = None

    WEATHER = 'weather_graphs'
    WEATHER_AVG = 'weather_avg'
    ASSESSMENTS = 'assess_graphs'
    ALL_ASS_DATA = 'all_ass_data'
    ASSESSMENT_VIEW = 'assessment_view'
    RESULT_SUMMARY = 'result_summary'
    KEY_ASSESS = 'key_assess'
    ONLY_TRIAL_DATA = 'OTD'
    TAG_UNKOWN = '??'

    def __init__(self, trialId, content, user,
                 trial=None, extra_id=None):
        if trial is not None:
            self._trial = trial
        else:
            self._trial = get_object_or_404(FieldTrial, pk=trialId)
        self._user = user
        self._extra_id = extra_id
        self._content = content
        self._assmts = None
        self._permisions = TrialPermission(self._trial, user)
        if content != TrialContent.ONLY_TRIAL_DATA:
            self._category = self._trial.product.category()
            self.getAssmts()

    def getMinMaxDate(self):
        self.getAssmts()
        if self._assmts:
            oneweek = timedelta(days=7)
            self._min_date = self._assmts.aggregate(
                min_date=Min('assessment_date'))['min_date']
            self._min_date -= oneweek
            self._max_date = self._assmts.aggregate(
                max_date=Max('assessment_date'))['max_date']
            self._max_date += oneweek
        else:
            self._min_date = None
            self._max_date = None
        return self._min_date, self._max_date

    def getMeteorology(self, getMeteoDataIfMissing=True):
        if self._trial.avg_temperature is None:
            if getMeteoDataIfMissing:
                # Let's try to fetch
                meteoData = self.fetchWeatherAvg()
                toSaved = False
                if meteoData['temp_avg'] != TrialContent.TAG_UNKOWN:
                    self._trial.avg_temperature = meteoData['temp_avg']
                    toSaved = True
                if meteoData['prep_avg'] != TrialContent.TAG_UNKOWN:
                    self._trial.avg_precipitation = meteoData['prep_avg']
                    toSaved = True
                if meteoData['hum_avg'] != TrialContent.TAG_UNKOWN:
                    self._trial.avg_humidity = meteoData['hum_avg']
                    toSaved = True
                if toSaved:
                    self._trial.save()
                return meteoData
            else:
                return {'dummy': '??'}
        else:
            return {
                'temp_avg': self._trial.avg_temperature,
                'prep_avg': self._trial.avg_precipitation,
                'hum_avg': self._trial.avg_humidity}

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
                controlNumber, keyThesisNumber = self.getControlKeyNumbers()
                graphF = DataGraphFactory(
                    level, assmts, dataPoints,
                    controlNumber=controlNumber,
                    keyThesisNumber=keyThesisNumber,
                    xAxis=xAxis, references=self._thesis)
                if type_graph == GraphTrial.LINE and len(assmts) == 1:
                    type_graph = GraphTrial.COLUMN
                graphs.append(
                    {'title': graphF.getTitle(),
                     'extra_title': _('efficacy'),
                     'content': graphF.draw(type_graph=type_graph)})
        return graphs

    def getWeatherData(self):
        minDate, maxDate = self.getMinMaxDate()
        Weather.enrich(minDate, maxDate,
                       self._trial.latitude,
                       self._trial.longitude)
        return Weather.objects.filter(
            date__range=(minDate, maxDate),
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
        temp_avg = TrialContent.TAG_UNKOWN
        hum_avg = TrialContent.TAG_UNKOWN
        prep_avg = TrialContent.TAG_UNKOWN
        minDate, maxDate = self.getMinMaxDate()
        avgData = Weather.objects.filter(
            date__range=(minDate, maxDate),
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

    def getRateTypeUnitsAndParts(self):
        self._thesis = Thesis.getObjects(self._trial, as_dict=True)
        self._assmts = Assessment.getObjects(self._trial)
        rateSets = Assessment.getRateSets(self._assmts)
        ratedParts = Assessment.getRatedParts(self._assmts)
        return rateSets, ratedParts

    def fetchAssessment(self):
        assessment = None
        if self._extra_id:
            assessment = Assessment.objects.get(id=self._extra_id)
        else:
            assmts = Assessment.getObjects(self._trial)
            if not assmts:
                return {'error': _('No assessements yet')}
            assessment = assmts[0]
        # Add additional data to the context
        trialPermision = TrialPermission(
            assessment.field_trial,
            self._user)
        dataHelper = DataHelper(assessment,
                                trialPermision.canEdit())
        return {'assessment': assessment,
                'rateunitpart': assessment.getUnitPartTitle(),
                **dataHelper.showDataAssessment(),
                **trialPermision.getPermisions()}

    def fetchAssessmentsData(self):
        rateSets, ratedParts = self.getRateTypeUnitsAndParts()
        return self.getAssGraphData(
            rateSets, ratedParts, GraphTrial.LINE, showEfficacy=False,
            xAxis=GraphTrial.L_DATE)

    def fetchResultSummaryData(self):
        rateSets, ratedParts = self.getRateTypeUnitsAndParts()
        return self.getAssGraphData(
            rateSets, ratedParts, GraphTrial.COLUMN, showEfficacy=True,
            xAxis=GraphTrial.L_ASSMT)

    def fetchAllAssessData(self):
        helper = DataTrialHelper(self._trial)
        return {**helper.getTrialData()}

    def fetchKeyAssessData(self):
        content = self.getKeyGraphData()

        if content:
            return content
        else:
            error = _("Efficacy cannot be determined yet."
                      "Data is not available,"
                      "key thesis or untreated thesis are not well identified,"
                      "key rate type unit is not well identified.")
            return {'error': error, 'trial': self._trial}

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
        if not self._trial.control_thesis or force:
            # if control_thesis is not designated yet, we nomine one
            # simple idea, use the first treatment pointed to the untreated
            for thesis in self.getThesis():
                treatments = TreatmentThesis.getObjects(thesis)
                for ttreatment in treatments:
                    if ttreatment.treatment.batch.product_variant.product.name == UNTREATED: # noqa E501
                        self._trial.control_thesis = ttreatment.thesis.id
                        self._trial.save()
                        break
        return self._trial.control_thesis

    def whatIsBestEfficacy(self, bestEfficacy, keyAssessmentId, force=False):
        if self._trial.best_efficacy != bestEfficacy and force:
            self._trial.best_efficacy = bestEfficacy
            self._trial.key_assessment = keyAssessmentId
            self._trial.save()
        return self._trial.best_efficacy

    def getKeyAssData(self):
        if not self._keyRateTypeUnit or not self._keyPartRated or\
           not self._keyThesisId or not self._untreatedThesisId:
            return None

        dataPoints = ReplicaData.dataPointsKeyAssessAvg(
            self._keyRateTypeUnit, self._keyPartRated,
            self._keyThesisId, self._untreatedThesisId)

        if len(dataPoints) > 1:
            return dataPoints
        else:
            return None

    def getKeyAssmts(self):
        return Assessment.objects.filter(
            rate_type_id=self._keyRateTypeUnit.id,
            part_rated=self._keyPartRated)

    def getKeyEfficacyComponents(self):
        self._keyRateTypeUnit, self._keyPartRated = self.whatIsKeyRates()
        self._keyThesisId = self.whatIsKeyThesis()
        self._untreatedThesisId = self.whatIsControlThesis()
        dataPoints = self.getKeyAssData()

        if not dataPoints:
            return None

        self._assmts = self.getKeyAssmts()
        return dataPoints

    def getControlKeyNumbers(self):
        controlNumber = None
        keyThesisNumber = None
        if self._trial.control_thesis:
            thesis = Thesis.objects.get(id=self._trial.control_thesis)
            controlNumber = thesis.number
        if self._trial.key_thesis:
            thesis = Thesis.objects.get(id=self._trial.key_thesis)
            keyThesisNumber = thesis.number
        return controlNumber, keyThesisNumber

    def getKeyGraphData(self):
        dataPoints = self.getKeyEfficacyComponents()
        if not dataPoints:
            return None
        bestEfficacy, line, kAssId = self.calculateBestEfficacy(
            dataPoints)
        keyThesis = Thesis.objects.get(id=self._keyThesisId)
        untreatedThesis = Thesis.objects.get(id=self._untreatedThesisId)
        thesiss = {
            self._keyThesisId: keyThesis,
            self._untreatedThesisId: untreatedThesis}
        graphF = DataGraphFactory(
            GraphTrial.L_REPLICA, self._assmts, dataPoints,
            showLegend=False,
            references=thesiss)
        num_assmts = len(self._assmts)
        graphF.addLineColorsToTraces(keyThesis.number,
                                     untreatedThesis.number)
        if num_assmts > 1:
            graphF.addTrace(line, "best efficacy")
        content = graphF.drawConclusionGraph(num_assmts)
        explanation = self.bestEfficiencyExplanation(
            self._keyRateTypeUnit, self._keyPartRated)

        if bestEfficacy:
            self.whatIsBestEfficacy(bestEfficacy, kAssId, force=True)
        return {'conclusion_graph': content,
                'key_treatment_product': keyThesis.getKeyProduct(),
                'unit_name': self._keyRateTypeUnit.getName(),
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

    def computeOnKeyAssessment(self, dataPoints):
        keyAssId = self._trial.key_assessment
        valueK = None
        valueC = None
        ddate = None
        for assm in self._assmts:
            if assm.id == keyAssId:
                ddate = assm.assessment_date
                break

        for point in dataPoints:
            if point['assessment__id'] == keyAssId:
                if point['reference__thesis__id'] == self._keyThesisId:
                    valueK = point['value']
                elif point['reference__thesis__id'] == self._untreatedThesisId:
                    valueC = point['value']
                if valueK and valueC:
                    break

        if valueK and valueC:
            bestEfficacy = self.calculateEfficacy(valueC, valueK)
            if self._trial.best_efficacy != bestEfficacy:
                self._trial.best_efficacy = bestEfficacy
                self._trial.save()
            lines = {'y': [round(valueC, 2), round(valueK, 2)],
                     'x': [ddate, ddate]}
            return bestEfficacy, lines, keyAssId
        return None, None, None

    def calculateBestEfficacy(self, dataPoints, force=False):
        if self._trial.key_assessment and not force:
            return self.computeOnKeyAssessment(dataPoints)
        else:
            return self.computeBestEfficacy(dataPoints)

    def computeBestEfficacy(self, dataPoints):
        bestEfficacy = 0
        dateMaxDistance = None
        pointC = None
        pointK = None
        values = {}
        assmtsDates = {assm.id: assm.assessment_date for assm in self._assmts}
        keyAssmtId = None
        for point in dataPoints:
            ddate = assmtsDates[point['assessment__id']]
            thesisId = point['reference__thesis__id']
            if ddate not in values:
                values[ddate] = {}
            if thesisId == self._keyThesisId:
                values[ddate]['k'] = point['value']
            if thesisId == self._untreatedThesisId:
                values[ddate]['c'] = point['value']
            values[ddate]['assId'] = point['assessment__id']
        for ddate in values:
            value = values[ddate]
            if 'k' not in value or 'c' not in value:
                continue
            thisEfficacy = self.calculateEfficacy(value['c'], value['k'])
            if thisEfficacy > bestEfficacy:
                bestEfficacy = thisEfficacy
                dateMaxDistance = ddate
                pointC = value['c']
                pointK = value['k']
                keyAssmtId = value['assId']

        if bestEfficacy > 0:
            lines = {'y': [round(pointC, 2), round(pointK, 2)],
                     'x': [dateMaxDistance, dateMaxDistance]}
            return bestEfficacy, lines, keyAssmtId
        else:
            return None, None, None

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
        ALL_ASS_DATA: fetchAllAssessData,
        ASSESSMENTS: fetchAssessmentsData,
        WEATHER_AVG: getMeteorology,
        ASSESSMENT_VIEW: fetchAssessment,
        RESULT_SUMMARY: fetchResultSummaryData}

    TEMPLATE_CARDS = 'trialapp/trial_content_cards.html'
    TEMPLATE_DIVS = 'trialapp/trial_content_divs.html'
    TEMPLATE_CONCLUSION_GRAPH = 'trialapp/trial_conclusion_graph.html'

    FETCH_TEMPLATES = {
        ASSESSMENT_VIEW: 'trialapp/trial_assessment_view.html',
        WEATHER: TEMPLATE_CARDS,
        KEY_ASSESS: TEMPLATE_CONCLUSION_GRAPH,
        ASSESSMENTS: TEMPLATE_CARDS,
        WEATHER_AVG: 'trialapp/trial_weather_avg.html',
        ALL_ASS_DATA: 'trialapp/trial_data_table.html',
        RESULT_SUMMARY: TEMPLATE_CARDS}

    def fetch(self):
        theFetch = TrialContent.FETCH_FUNCTIONS.get(
            self._content, TrialContent.fetchDefault)
        content = theFetch(self)
        template = TrialContent.FETCH_TEMPLATES.get(
            self._content, TrialContent.TEMPLATE_CARDS)
        return render(self._request, template,
                      {'dataContent': content,
                       **self._permisions.getPermisions()})


@login_required
def trialContentApi(request):
    trialId = int(request.GET.get('id', 0))
    content = request.GET.get('content_type')
    extra_id = request.GET.get('extra_id', None)
    return TrialContent(trialId, content,
                        request.user, extra_id=extra_id).fetch()


class SetTrialKeyValues(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    TAG_KEY_THESIS = 'key_thesis'
    TAG_CONTROL = 'control_thesis'
    TAG_RATE_TYPE = 'key_rate_type'
    TAG_RATED_PART = 'key_rated_part'
    TAG_ASSESSMENT = 'key_assessment'

    # see generateDataPointId
    def post(self, request, trial_id, type_param):
        itemId = request.POST['item_id']
        trial = get_object_or_404(FieldTrial, pk=trial_id)
        if type_param == SetTrialKeyValues.TAG_KEY_THESIS:
            trial.key_thesis = int(itemId)
        elif type_param == SetTrialKeyValues.TAG_CONTROL:
            trial.control_thesis = int(itemId)
        elif type_param == SetTrialKeyValues.TAG_RATE_TYPE:
            trial.key_ratetypeunit_id = int(itemId)
        elif type_param == SetTrialKeyValues.TAG_RATED_PART:
            trial.key_ratedpart = itemId
        elif type_param == SetTrialKeyValues.TAG_ASSESSMENT:
            trial.key_assessment = int(itemId)
        trial.save()
        # DO we need to FORCE TO COMPUTE EFFICACY???
        # calculate best efficacy
        return redirect('thesis-list', field_trial_id=trial_id)
