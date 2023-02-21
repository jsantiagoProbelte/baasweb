from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis,\
    TrialAssessmentSet, AssessmentType, AssessmentUnit
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.fieldtrial_views import editNewFieldTrial, saveFieldTrial,\
    FieldTrialApi, FieldTrialListView, FieldTrialDeleteView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class FieldTrialViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_trialapp_index(self):
        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)

        self.assertContains(response, 'Field Trials')
        self.assertContains(response, 'No Field Trial yet.')

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)

        thesis = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertNotContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(
            response,
            'Please define types and units')

        TrialAssessmentSet.objects.create(
            field_trial=fieldTrial,
            type=AssessmentType.objects.get(pk=1),
            unit=AssessmentUnit.objects.get(pk=1))
        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        self.assertContains(response, '1 &#10000;</a>')  # Number thesis
        self.assertContains(response, '0 &#43;</a>')  # Number applications
        thesis.delete()
        fieldTrial.delete()

    def test_editfieldtrial(self):
        request = self._apiFactory.get('/edit_fieldtrial')
        self._apiFactory.setUser(request)
        response = editNewFieldTrial(request)
        self.assertContains(response, 'create-field-trial')
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        fieldTrialData = TrialAppModelTest.FIELDTRIALS[0]
        request = self._apiFactory.post(
            '/save_fieldtrial', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = saveFieldTrial(request)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.name, fieldTrialData['name'])
        self.assertEqual(response.status_code, 302)

        request = self._apiFactory.get(
            '/edit_fieldtrial/{}'.format(fieldTrial.id))
        self._apiFactory.setUser(request)
        response = editNewFieldTrial(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-field-trial')
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        fieldTrialData['field_trial_id'] = fieldTrial.id
        fieldTrialData['responsible'] = newresponsible

        request = self._apiFactory.post(
            '/save_fieldtrial', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = saveFieldTrial(request, field_trial_id=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

        fieldTrialData['field_trial_id'] = fieldTrial.id
        fieldTrialData['samples_per_replica'] = '3'
        self.assertEqual(fieldTrial.samples_per_replica, None)
        request = self._apiFactory.post(
            '/save_fieldtrial', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = saveFieldTrial(request, field_trial_id=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.samples_per_replica, 3)
        self.assertEqual(response.status_code, 302)

    def test_showFieldTrial(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

        # path = reverse('field_trial_api',
        #                kwargs={'field_trial_id': fieldTrial.id})
        request = self._apiFactory.get('field_trial_api')
        self._apiFactory.setUser(request)
        apiView = FieldTrialApi()
        response = apiView.get(request,
                               **{'field_trial_id': fieldTrial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)

        deleteRequest = self._apiFactory.get('fieldtrial-delete')
        self._apiFactory.setUser(deleteRequest)
        response = FieldTrialDeleteView.as_view()(deleteRequest,
                                                  pk=fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)
