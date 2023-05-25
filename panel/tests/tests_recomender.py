from django.test import TestCase
from baaswebapp.tests.test_views import ApiRequestHelperTest
from panel.recomender import RecomenderApi


class RecommenderTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()

    def test_recomender_api(self):
        request = self._apiFactory.get('recomender')
        self._apiFactory.setUser(request)
        response = RecomenderApi.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        request = self._apiFactory.get(
            'recomender', {'latitude': 90, 'longitude': 90})
        self._apiFactory.setUser(request)
        response = RecomenderApi.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Weather')
        self.assertContains(response, 'Alerts')
