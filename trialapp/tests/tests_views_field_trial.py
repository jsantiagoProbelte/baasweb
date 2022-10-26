from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, TrialDbInitialLoader
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory
from trialapp.fieldtrial_views import editNewFieldTrial, saveFieldTrial


class FieldTrialViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()

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
        fieldTrialData = TrialAppModelTest.FIELDTRIALS[0]
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
