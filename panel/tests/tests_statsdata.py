from django.test import TestCase
from baaswebapp.tests.test_views import ApiRequestHelperTest
from baaswebapp.data_loaders import TrialDbInitialLoader
from panel.statsdata import StatsDataApi
from panel.quality_panel import ThesisPanelApi
from trialapp.models import FieldTrial, Thesis, TreatmentThesis
from baaswebapp.tests.tests_helpers import TrialTestData
from catalogue.models import Product, Treatment, RateUnit


class StatsDataTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        product = Product.objects.create(name='A product')
        rateUnit = RateUnit.objects.create(name='unit')

        cdata = {"name": 'pppp', 'rate': 1, 'rate_unit_id': rateUnit.id,
                 'product_id': product.id}
        treat = Treatment.objects.create(**cdata)
        for trialData in TrialTestData.TRIALS:
            FieldTrial.createTrial(**trialData)
            for thesis in TrialTestData.THESIS:
                thesis = Thesis.createThesis(**thesis)
                if thesis.id > 1:
                    # Create some without treatment
                    TreatmentThesis.objects.create(
                        thesis=thesis, treatment=treat)

    def test_statsdata_api(self):
        request = self._apiFactory.get('statsdata')
        self._apiFactory.setUser(request)
        response = StatsDataApi.as_view()(request)
        self.assertEqual(response.status_code, 200)
        counts = FieldTrial.objects.count()
        self.assertTrue(counts > 0)
        self.assertContains(response, '{} total trials'.format(counts))

    def test_quality_panel(self):
        request = self._apiFactory.get('thesis_quality_panel')
        self._apiFactory.setUser(request)
        response = ThesisPanelApi.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '(1) total trials (1) thesis')
