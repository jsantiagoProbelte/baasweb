from django.test import TestCase
from django.urls import reverse


class BaaSWebAppTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_baaswebapp_index(self):
        # Get second page and confirm it has (exactly) remaining 3 items
        response = self.client.get(reverse('baaswebapp_index'))

        self.assertContains(response, 'BaaS in mode DEBUG= True')
