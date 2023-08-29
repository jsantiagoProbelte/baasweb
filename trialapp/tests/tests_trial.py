from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial
from trialapp.tests.tests_helpers import TrialAppModelData
from trialapp.trial_views import TrialApi
from baaswebapp.tests.test_views import ApiRequestHelperTest


class TrialViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()



    def test_showFieldTrial(self):
        trial = FieldTrial.create_fieldTrial(
            **TrialAppModelData.FIELDTRIALS[0])

        request = self._apiFactory.get('trial_api')
        self._apiFactory.setUser(request)
        response = TrialApi.as_view()(request, pk=trial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trial.code)

