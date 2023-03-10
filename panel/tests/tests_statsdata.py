from django.test import TestCase
from baaswebapp.tests.test_views import ApiRequestHelperTest
from baaswebapp.data_loaders import TrialDbInitialLoader
from panel.statsdata import StatsDataApi
from trialapp.models import FieldTrial
from trialapp.tests.tests_models import TrialAppModelTest


class StatsDataTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        for trialData in TrialAppModelTest.FIELDTRIALS:
            FieldTrial.create_fieldTrial(**trialData)

    def test_statsdata_api(self):
        # Creating thesis , but not with all attributres
        request = self._apiFactory.get('statsdata')
        self._apiFactory.setUser(request)
        response = StatsDataApi.as_view()(request)
        self.assertEqual(response.status_code, 200)
        counts = FieldTrial.objects.count()
        self.assertTrue(counts > 0)
        self.assertContains(response, '({}) total trials'.format(counts))
