from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial
from trialapp.tests.tests_models import FieldAppTest
from django.test import RequestFactory
from trialapp.views import editNewFieldTrial, saveFieldTrial


class TrialAppTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        FieldAppTest.setUpTestData()

    def test_trialapp_index(self):
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertContains(response, 'Field Trials')
#        self.assertContains(response, FieldAppTest.FIELD_TEST_LIST[0])

    def test_editfieldtrial(self):
        request_factory = RequestFactory()
        # request = request_factory.post('/fake-path', data={'name': u'Waldo'})
        request = request_factory.get('/edit_fieldtrial')
        response = editNewFieldTrial(request)
        self.assertContains(response, 'create-field-trial')
        self.assertContains(response, 'New Field Trial')
        self.assertNotContains(response, 'Edit Field Trial')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        fieldTrialData = {
            'name': 'fieldTrial 666',
            'phase': 1,
            'objective': 1,
            'responsible': 'Waldo',
            'product': 1,
            'project': 1,
            'crop': 1,
            'plague': 1,
            'initiation_date': '2021-07-01',
            'farmer': 'Mr Farmer',
            'location': 'La Finca'
        }
        request = request_factory.post('/save_fieldtrial', data=fieldTrialData)
        response = saveFieldTrial(request)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.name, fieldTrialData['name'])
        self.assertEqual(response.status_code, 302)

        request = request_factory.get(
            '/edit_fieldtrial/{}'.format(fieldTrial.id))
        response = editNewFieldTrial(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-field-trial')
        self.assertNotContains(response, 'New Field Trial')
        self.assertContains(response, 'Edit Field Trial')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        fieldTrialData['field_trial_id'] = fieldTrial.id
        fieldTrialData['responsible'] = newresponsible
        request = request_factory.post('/save_fieldtrial', data=fieldTrialData)
        response = saveFieldTrial(request, field_trial_id=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)
