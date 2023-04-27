from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial
from trialapp.tests.tests_models import TrialAppModelTest
from labapp.labtrial_views import LabTrialView
from labapp.labtrial_views import LabTrialCreateView,\
    LabTrialUpdateView, LabTrialListView


from baaswebapp.tests.test_views import ApiRequestHelperTest


class LabTrialViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_trialapp_index(self):
        request = self._apiFactory.get('labtrial-list')
        self._apiFactory.setUser(request)
        response = LabTrialListView.as_view()(request)

        self.assertContains(response, 'Lab trials')
        self.assertContains(response, 'No Trials yet.')

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        fieldTrial.trial_meta = FieldTrial.TrialMeta.LAB_TRIAL
        fieldTrial.samples_per_replica = 20
        fieldTrial.save()

        request = self._apiFactory.get('labtrial-list')
        self._apiFactory.setUser(request)
        response = LabTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Trials yet.')
        self.assertContains(response, fieldTrial.name)
        fieldTrial.delete()

    def test_createFieldtrial(self):
        request = self._apiFactory.get('labtrial-add')
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        fieldTrialData = TrialAppModelTest.FIELDTRIALS[0].copy()
        fieldTrialData['samples_per_replica'] = 24
        request = self._apiFactory.post(
            'labtrial-add', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        # it is missing a code.
        fieldTrialData['code'] = '19701409'
        request = self._apiFactory.post(
            'labtrial-add', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.name, fieldTrialData['name'])
        self.assertTrue(fieldTrial.code is not None)

        request = self._apiFactory.get('labtrial-update')
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        fieldTrialData['responsible'] = newresponsible

        request = self._apiFactory.post(
            'labtrial-update', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

        fieldTrialData['samples_per_replica'] = '3'
        self.assertEqual(fieldTrial.samples_per_replica, 24)
        request = self._apiFactory.post(
            'labtrial-update', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.samples_per_replica, 3)
        self.assertEqual(response.status_code, 302)

        request = self._apiFactory.get('labtrial-show')
        self._apiFactory.setUser(request)
        apiView = LabTrialView()
        response = apiView.get(request,
                               pk=fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'lab trial')
