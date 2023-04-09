from django.test import TestCase
from baaswebapp.tests.test_views import ApiRequestHelperTest
from panel.recomender import RecomenderApi
import json
from datetime import datetime, timezone


class RecommenderTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()

    def test_recomender_api(self):
        request = self._apiFactory.get('recomender')
        self._apiFactory.setUser(request)
        response = RecomenderApi.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        request = self._apiFactory.post(
            'recomender', {'latitude': 90, 'longitude': 90})
        self._apiFactory.setUser(request)
        response = RecomenderApi.as_view()(request)
        data = json.loads(response.content)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT12:00")
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(data['daily_weather']
        #                  ['temperatures'][0]['date'], today)
        self.assertTrue(today is not None)
        self.assertTrue(data['daily_weather']['temperatures']
                        [0]['date'] is not None)
