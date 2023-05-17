from django.test import TestCase, Client
from baaswebapp.meteo_api import MeteoApi
from datetime import datetime


class TestAssessment():
    def __init__(self):
        self.assessment_date = datetime.strptime(
            '2023-01-01', '%Y-%m-%d').date()


class TestFieldTrial():
    def __init__(self):
        self.longitude = "1"
        self.latitude = "1"


class MeteoApiTest(TestCase):

    _apiFactory = None

    def test_new(self):
        meteo_api = MeteoApi()
        test_assessment = TestAssessment()
        test_fieldtrial = TestFieldTrial()
        meteo_api.enrich_assessment(test_assessment, test_fieldtrial)
