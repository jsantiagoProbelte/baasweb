import json
from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from baaswebapp.models import RateTypeUnit
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.data_models import Assessment
from trialapp.models import FieldTrial, Thesis
from trialapp.map_utils import MapApi
from trialapp.tests.tests_models import TrialAppModelTest


class MapApiTestCase(TestCase):
    _apiFactory = None

    FIELDTRIALS = [{
        'name': 'fieldTrial 666',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 1,
        'crop': 1,
        'plague': 1,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3,
        'latitude': 38.2796,
        'longitude': -0.7914},
        {
        'name': 'fieldTrial 999',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 1,
        'crop': 2,
        'plague': 2,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3,
        'latitude': 41.5432,
        'longitude': 2.1098},
        {
        'name': 'fieldTrial 333',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 2,
        'crop': 1,
        'plague': 2,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3},
    ]
    _products = []
    _fieldTrials = []
    _theses = []
    _assessments = []
    _units = []

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        for fieldTrialInfo in MapApiTestCase.FIELDTRIALS:
            self._fieldTrials.append(
                FieldTrial.create_fieldTrial(**fieldTrialInfo))

        # for fieldTrial in self._fieldTrials:
        for thesis in TrialAppModelTest.THESIS:
            # thesis['field_trial_id'] = fieldTrial.id
            self._theses.append(Thesis.create_Thesis(**thesis))

        rateTypes = RateTypeUnit.objects.all()
        self._units = [rateTypes[i] for i in range(1, 4)]

        self._assessments = [Assessment.objects.create(
            name='eval{}'.format(i),
            assessment_date='2023-0{}-15'.format(i),
            rate_type=self._units[0],
            field_trial=self._fieldTrials[0],
            crop_stage_majority=65+i) for i in range(1, 3)]

    def test_map_api_post(self):
        data = [1, 2]
        request = self._apiFactory.post('coordinates', data=json.dumps(data), content_type='application/json')
        self._apiFactory.setUser(request)
        response = MapApi.as_view()(request)

        self.assertEqual(response.status_code, 200)
        print(response.content)
        response_data = json.loads(response.content)
        self.assertIn('coordinates', response_data)
        self.assertEqual(len(response_data['coordinates']), 2)
        self.assertEqual(response_data['coordinates'], [['-0.7914', '38.2796'], ['2.1098', '41.5432']])

