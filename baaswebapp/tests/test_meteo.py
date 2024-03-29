from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from baaswebapp.meteo_api import MeteoApi
from datetime import datetime
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.models import FieldTrial
from baaswebapp.tests.tests_helpers import TrialTestData


class TestAssessment():
    def __init__(self):
        self.assessment_date = datetime.strptime(
            '2023-01-01', '%Y-%m-%d').date()


class TestFieldTrial():
    def __init__(self):
        self.longitude = "1.0193322"
        self.latitude = "0.99212605"


class MeteoApiTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_new(self):
        meteo_api = MeteoApi()
        test_assessment = TestAssessment()
        test_fieldtrial = TestFieldTrial()
        res = meteo_api.enrich_assessment(test_assessment, test_fieldtrial)
        assert (not res.recent)
        assert (res.max_temp == 28.0)
        assert (res.soil_temp_100_to_255cm == 29.058333333333334)
        assert (res.precipitation_hours == 0.0)

    def test_existing(self):
        meteo_api = MeteoApi()
        test_assessment = TestAssessment()
        test_fieldtrial = TestFieldTrial()
        res = meteo_api.enrich_assessment(test_assessment, test_fieldtrial)

        res2 = meteo_api.enrich_assessment(test_assessment, test_fieldtrial)
        assert (not res.recent)
        assert (res.max_temp == float(str(res2.max_temp)))
        assert abs(res.soil_temp_100_to_255cm -
                   float(str(res2.soil_temp_100_to_255cm))) < 0.1

        assert (float(res.precipitation_hours) ==
                float(str(res2.precipitation_hours)))

    def test_req(self):
        request = self._apiFactory.get('meteo_api')
        self._apiFactory.setUser(request)
        meteo_api = MeteoApi()
        trial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        response = meteo_api.get(request,
                                 field_trial_id=trial.id)

        assert (response.status_code == 302)
