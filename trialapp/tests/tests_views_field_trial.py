from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, Thesis, TrialDbInitialLoader
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory
from trialapp.fieldtrial_views import editNewFieldTrial, saveFieldTrial,\
    showFieldTrial


class FieldTrialViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_trialapp_index(self):
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertContains(response, 'Field Trials')
        self.assertContains(response, 'No Field Trial yet.')

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

        response = self.client.get(reverse('fieldtrial-list'))
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)

        thesis = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertNotContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, '1 &#10000;</a>')  # Number thesis
        self.assertContains(response, '0 &#43;</a>')  # Number applications
        thesis.delete()
        fieldTrial.delete()

    def test_editfieldtrial(self):
        request_factory = RequestFactory()
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
        print(fieldTrialData)
        response = saveFieldTrial(request, field_trial_id=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

    def test_showFieldTrial(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        request_factory = RequestFactory()
        request = request_factory.get(
            '/show_fieldtrial')
        response = showFieldTrial(request, field_trial_id=fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)
