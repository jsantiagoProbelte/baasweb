from django.test import TestCase
from django.urls import reverse
from trialapp.tests.tests_models import FieldAppTest


class TrialAppTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_trialapp_index(self):
        FieldAppTest.setUpTestData()
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertContains(response, 'Field Trial List')
#        self.assertContains(response, FieldAppTest.FIELD_TEST_LIST[0])
