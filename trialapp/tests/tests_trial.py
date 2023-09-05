from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from baaswebapp.models import PType, RateTypeUnit
from catalogue.models import Product, Vendor, Batch, Treatment, \
    ProductVariant, UNTREATED
from trialapp.models import FieldTrial, Thesis, TreatmentThesis, RateUnit, \
    Application, PartRated
from trialapp.data_models import Assessment, ReplicaData, Replica
from trialapp.tests.tests_helpers import TrialTestData
from trialapp.trial_views import TrialApi, TrialContent, trialContentApi, \
    SetTrialKeyValues
from baaswebapp.tests.test_views import ApiRequestHelperTest
from datetime import timedelta, datetime


class TrialViewsTest(TestCase):
    _apiFactory = None
    CONTROL_VALUE = 100
    FIRST_MIN_VALUE = 40
    LAST_MIN_VALUE = 20

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._trial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        # see createCatalogue. Here we are setting the product on the trial
        # to a CONTROL type. This will have implications on how
        # efficacy is calculated

    def test_showFieldTrial(self):
        self.createObjects()
        request = self._apiFactory.get('trial_api')
        self._apiFactory.setUser(request)
        response = TrialApi.as_view()(request, pk=self._trial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self._trial.code)

    def createThesisData(self, name, productId, seed, decrease, numReplicas=4):
        thesisInfo = TrialTestData.THESIS[0].copy()
        thesisInfo['name'] = name
        thesis = Thesis.createThesis(**thesisInfo)
        replicas = Replica.createReplicas(thesis, numReplicas)
        value = seed
        for replica in replicas:
            for ass in self._assmts:
                ReplicaData.objects.create(
                    value=seed, reference_id=replica, assessment=ass)
                value -= decrease
        TreatmentThesis.objects.create(
            thesis=thesis,
            treatment=self._treatments[productId])
        return thesis

    def addAssessment(self, id, currentDate):
        assModel = TrialTestData.ASSESSMENT[0].copy()
        rateTypeUnit = RateTypeUnit.objects.get(id=id)
        assModel['rate_type'] = rateTypeUnit
        assModel['assessment_date'] = currentDate.date()
        ass = Assessment.objects.create(**assModel)
        TrialTestData.addWeatherData(ass)
        return ass

    def createAssmts(self, numUnits=2, numAss=3):
        self._assmts = []
        oneweek = timedelta(days=7)
        self._firstRateTypeUnitId = 2
        for u in range(numUnits):
            currentDate = datetime(2022, 7, 1)
            for aaI in range(numAss):
                id = (u + self._firstRateTypeUnitId)
                self._assmts.append(self.addAssessment(id, currentDate))
                currentDate += oneweek

    def createThesis(self):
        # Create Thesis & Data
        self._controlThesis = self.createThesisData(
            'Control', self._untreated.id,
            TrialViewsTest.CONTROL_VALUE, 0)
        for t in range(3):
            self.createThesisData(
                f'KeyThesis{t}', self._other.id,
                TrialViewsTest.FIRST_MIN_VALUE, t)

        # The decrease to 1 should get better that the first of the previous
        # 3 thesis, equal than 2 and worst than the 3, but it will have
        # a product of Probelte,so it alsway be keyThesis
        self._keyThesis = self.createThesisData(
            'KeyThesis', self._botribel.id,
            TrialViewsTest.FIRST_MIN_VALUE, 1)

    def createCatalogue(self):
        unit = RateUnit.objects.get(id=1)
        vendor1 = Vendor.objects.get(id=1)
        vendor1.key_vendor = True
        vendor1.save()
        self._botribel = Product.objects.get(id=2)
        self._botribel.type_product = PType.FUNGICIDE
        self._botribel.vendor = vendor1
        self._botribel.save()
        self._trial.product = self._botribel
        self._trial.save()
        self._other = Product.objects.get(id=3)
        self._other.vendor = Vendor.objects.get(id=2)
        self._other.save()
        self._untreated = Product.objects.filter(name=UNTREATED)[0]
        self._treatments = {}
        for prod in [self._untreated, self._botribel, self._other]:
            pv = ProductVariant.createDefault(prod)
            batch = Batch.createDefault(pv)
            self._treatments[prod.id] = Treatment.objects.create(
                name=prod.name, rate=33, rate_unit=unit, batch=batch)

    def createApplications(self):
        for ass in self._assmts:
            Application.objects.create(
                app_date=ass.assessment_date,
                field_trial=self._trial,
                bbch=ass.crop_stage_majority)

    def createObjects(self):
        self.createCatalogue()
        self.createAssmts()
        self.createThesis()

    def test_discoverKeyInfo(self):

        self.createObjects()
        trialH = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        self.assertEqual(trialH.whatIsControlThesis(), self._controlThesis.id)
        self.assertEqual(trialH.whatIsKeyThesis(), self._keyThesis.id)
        self._trial = FieldTrial.objects.get(id=self._trial.id)
        self.assertEqual(self._trial.key_thesis, self._keyThesis.id)
        self.assertEqual(self._trial.control_thesis, self._controlThesis.id)

        # validate that if there is data, even if it is wrong it  not check it
        self._trial.key_thesis = 66
        self._trial.control_thesis = 66
        self._trial.save()
        trialH = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        self.assertEqual(trialH.whatIsControlThesis(), 66)
        self.assertEqual(trialH.whatIsKeyThesis(), 66)

        self.assertEqual(trialH.whatIsControlThesis(force=True),
                         self._controlThesis.id)
        self.assertEqual(trialH.whatIsKeyThesis(force=True),
                         self._keyThesis.id)
        self._trial = FieldTrial.objects.get(id=self._trial.id)
        self.assertEqual(trialH.whatIsBestEfficacy(1, 1), None)
        checkTrial = FieldTrial.objects.get(id=self._trial.id)
        self.assertTrue(checkTrial.key_assessment is None)
        self.assertTrue(checkTrial.best_efficacy is None)
        self.assertEqual(trialH.whatIsBestEfficacy(1, 1, force=True), 1)
        checkTrial = FieldTrial.objects.get(id=self._trial.id)
        self.assertEqual(checkTrial.key_assessment, 1)
        self.assertTrue(checkTrial.best_efficacy, 1)

        keyRate, keyPart = trialH.whatIsKeyRates()
        self.assertEqual(keyRate.id, self._firstRateTypeUnitId)
        # ... because all of the them are equal

        # Now let's calculate best efficacy
        dataPoints = trialH.getKeyEfficacyComponents()
        bestEfficacy, line, kAssId = trialH.computeBestEfficacy(dataPoints)
        firstExpectedEff = trialH.calculateEfficacy(
            TrialViewsTest.CONTROL_VALUE, TrialViewsTest.FIRST_MIN_VALUE)
        self.assertEqual(bestEfficacy, firstExpectedEff)

        content = trialH.fetchKeyAssessData()

        self.assertTrue('bestEfficacy' in content)
        self.assertEqual(bestEfficacy, content['bestEfficacy'])
        self.assertEqual(content['control_value'], line['y'][0])
        self.assertEqual(content['best_keytesis_value'], line['y'][1])

        # let's add one on other RateTypeUnit
        self._trial = FieldTrial.objects.get(id=self._trial.id)
        keyRateTypeUnitId = self._firstRateTypeUnitId + 1
        newAss = self.addAssessment(keyRateTypeUnitId, datetime(2022, 12, 1))
        for replica in Replica.objects.all():
            value = TrialViewsTest.LAST_MIN_VALUE
            if self._controlThesis.id == replica.thesis.id:
                value = TrialViewsTest.CONTROL_VALUE
            ReplicaData.objects.create(
                value=value,
                reference=replica, assessment=newAss)
        trialH.getAssmts(force=True)
        keyRate, keyPart = trialH.whatIsKeyRates(force=True)
        self.assertEqual(keyRate.id, keyRateTypeUnitId)

        # if we calculate the efficacy is going to change
        # after adding the assessment
        self._trial = FieldTrial.objects.get(id=self._trial.id)
        self._trial.key_assessment = None
        self._trial.save()
        tContent = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        content = tContent.fetchKeyAssessData()
        secondEfficacyExpected = tContent.calculateEfficacy(
            TrialViewsTest.CONTROL_VALUE, TrialViewsTest.LAST_MIN_VALUE)
        self.assertEqual(secondEfficacyExpected,
                         content['bestEfficacy'])
        checkTrial = FieldTrial.objects.get(id=self._trial.id)
        # it is an id, different from 1
        self.assertTrue(checkTrial.key_assessment > 1)

        # if we change the type of product to not be a control,
        # calculation of efficacy will change
        self._botribel.type_product = PType.FERTILIZER
        self._botribel.save()
        self._trial = FieldTrial.objects.get(id=self._trial.id)
        self._trial.key_assessment = None
        self._trial.save()
        tContent2 = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        thirdEfficacyExpected = tContent2.calculateEfficacy(
            TrialViewsTest.CONTROL_VALUE, TrialViewsTest.FIRST_MIN_VALUE)
        content2 = tContent2.fetchKeyAssessData()
        self.assertEqual(thirdEfficacyExpected,
                         content2['bestEfficacy'])
        # also realise that the first and the third efficacy, althouth the
        # input numbers are the same, the output is different becasue the
        # type of product is different
        self.assertNotEqual(secondEfficacyExpected, thirdEfficacyExpected)

    def test_computeBestEfficacy(self):
        self.createObjects()
        trialH = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        dataPoints = trialH.getKeyEfficacyComponents()
        efficacy, line, fAssmId = trialH.calculateBestEfficacy(dataPoints)
        self.assertTrue(efficacy is not None)
        self.assertTrue(fAssmId is not None)

        # Lets change to another assessment not optimal
        self._trial.key_assessment = fAssmId + 1
        self._trial.save()
        trialH2 = TrialContent(self._trial.id, TrialContent.KEY_ASSESS)
        dataPoints = trialH2.getKeyEfficacyComponents()
        efficacy2, line, fAssmId2 = trialH2.calculateBestEfficacy(dataPoints)
        self.assertTrue(fAssmId2 != fAssmId)

        efficacy3, line, fAssmId3 = trialH2.calculateBestEfficacy(dataPoints,
                                                                  force=True)
        self.assertTrue(fAssmId3 == fAssmId)

    def test_fetches(self):
        # Fetch content before data is created.. to go through empty statments
        for typeContent in list(TrialContent.FETCH_FUNCTIONS.keys()):
            tContent = TrialContent(self._trial.id, typeContent)
            theFetch = TrialContent.FETCH_FUNCTIONS.get(
                typeContent, TrialContent.fetchDefault)
            theFetch(tContent)

        self.createObjects()
        # Try with the trialContentApi
        for content in list(TrialContent.FETCH_FUNCTIONS.keys()):
            data = {'id': self._trial.id,
                    'content_type': content}
            getRequest = self._apiFactory.get('trial_content',
                                              data=data)
            self._apiFactory.setUser(getRequest)
            response = trialContentApi(getRequest)
            self.assertEqual(response.status_code, 200)

    def callSetTrialKeyValues(self, item_id, type_param):
        addData = {'item_id': item_id}
        request = self._apiFactory.post(
            'set-trial-key-values',
            data=addData)
        self._apiFactory.setUser(request)
        apiView = SetTrialKeyValues()
        response = apiView.post(request, self._trial.id, type_param)
        self.assertEqual(response.status_code, 302)
        return FieldTrial.objects.get(id=self._trial.id)

    def test_setkeytrialvalues(self):
        item_id = 6
        self.assertTrue(self._trial.key_thesis is None)
        self._trial = self.callSetTrialKeyValues(
            item_id, SetTrialKeyValues.TAG_KEY_THESIS)
        self.assertEqual(self._trial.key_thesis, item_id)

        self.assertTrue(self._trial.control_thesis is None)
        self._trial = self.callSetTrialKeyValues(
            item_id, SetTrialKeyValues.TAG_CONTROL)
        self.assertEqual(self._trial.control_thesis, item_id)

        self.assertTrue(self._trial.key_ratetypeunit_id is None)
        self._trial = self.callSetTrialKeyValues(
            3, SetTrialKeyValues.TAG_RATE_TYPE)
        self.assertEqual(self._trial.key_ratetypeunit_id, 3)

        self.assertEqual(self._trial.key_ratedpart,
                         PartRated.UNDF.value)
        self._trial = self.callSetTrialKeyValues(
            PartRated.BUNCH.value, SetTrialKeyValues.TAG_RATED_PART)
        self.assertEqual(self._trial.key_ratedpart, PartRated.BUNCH.value)

        self.assertTrue(self._trial.key_assessment is None)
        self._trial = self.callSetTrialKeyValues(
            item_id, SetTrialKeyValues.TAG_ASSESSMENT)
        self.assertEqual(self._trial.key_assessment, item_id)
