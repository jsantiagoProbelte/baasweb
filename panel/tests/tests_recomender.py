from django.test import TestCase
from baaswebapp.tests.test_views import ApiRequestHelperTest
from panel.recomender import RecomenderApi


class RecommenderTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()

    def test_recomender_api(self):
        # Creating thesis , but not with all attributres
        request = self._apiFactory.get('recomender')
        self._apiFactory.setUser(request)
        response = RecomenderApi.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'var latitude=38.03467;')
        self.assertContains(response, 'var longitude=-1.189287;')
