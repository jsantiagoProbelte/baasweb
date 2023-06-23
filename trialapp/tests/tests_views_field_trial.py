from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Application, Replica
from trialapp.data_models import Assessment, ReplicaData
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.fieldtrial_views import FieldTrialCreateView, FieldTrialApi,\
    FieldTrialUpdateView, FieldTrialListView, FieldTrialDeleteView,\
    DownloadTrial
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.trial_helper import TrialHelper, PdfTrial
from baaswebapp.models import RateTypeUnit
import os


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
        self.assertContains(response, 'No Trials yet.')

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Trials yet.')
        self.assertContains(response, 'Field trials')
        self.assertContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)

        thesis = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Trials yet.')
        self.assertNotContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)

        request = self._apiFactory.get('fieldtrial-list')
        self._apiFactory.setUser(request)
        response = FieldTrialListView.as_view()(request)
        thesis.delete()
        fieldTrial.delete()

    def test_createFieldtrial(self):
        request = self._apiFactory.get('fieldtrial-add')
        self._apiFactory.setUser(request)
        response = FieldTrialCreateView.as_view()(request)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        fieldTrialData = TrialAppModelTest.FIELDTRIALS[0].copy()
        request = self._apiFactory.post(
            'fieldtrial-add', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = FieldTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        # it is missing a code.
        fieldTrialData['code'] = '19701409'
        request = self._apiFactory.post(
            'fieldtrial-add', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = FieldTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.name, fieldTrialData['name'])
        self.assertTrue(fieldTrial.code is not None)

        request = self._apiFactory.get('fieldtrial-update')
        self._apiFactory.setUser(request)
        response = FieldTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        fieldTrialData['responsible'] = newresponsible

        request = self._apiFactory.post(
            'fieldtrial-update', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = FieldTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

        fieldTrialData['samples_per_replica'] = '3'
        self.assertEqual(fieldTrial.samples_per_replica, 0)
        request = self._apiFactory.post(
            'fieldtrial-update', data=fieldTrialData)
        self._apiFactory.setUser(request)
        response = FieldTrialUpdateView.as_view()(
            request, pk=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.samples_per_replica, 3)
        self.assertEqual(response.status_code, 302)

    def createDataTrial(self):
        trial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        assessments = []
        for index in range(4):
            assessments.append(Assessment.objects.create(
                name=f'ass {index}',
                assessment_date=f'2023-0{index+1}-01',
                field_trial=trial,
                part_rated='Undefined',
                crop_stage_majority='Undefined',
                rate_type=RateTypeUnit.objects.get(id=1)))
        Application.objects.create(
            app_date='2023-01-01',
            field_trial=trial,
            bbch='69-96')
        replicas = {}
        nums = 4
        for j in range(nums):
            thesis = Thesis.objects.create(
                name='{}'.format(j),
                number=j,
                field_trial_id=trial.id)
            replicas[j] = Replica.createReplicas(thesis, nums)

        for tId in range(nums):
            for index in range(nums):
                for ass in assessments:
                    ReplicaData.objects.create(
                        assessment_id=ass.id,
                        reference_id=replicas[tId][index],
                        value=tId+index+ass.id)
        return trial

    def test_showFieldTrial(self):
        fieldTrial = self.createDataTrial()

        # Export file
        PdfTrial(fieldTrial).produce()
        trialFile = './{}_trial.pdf'.format(fieldTrial.code)
        self.assertTrue(os.path.exists(trialFile))

        # Download it
        request = self._apiFactory.get('download_pdf')
        self._apiFactory.setUser(request)
        apiView = DownloadTrial()
        response = apiView.get(request,
                               field_trial_id=fieldTrial.id)
        self.assertTrue(os.path.exists(trialFile))
        os.remove(trialFile)

        # Assert that the response has a status code of 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Assert that the response has the correct content type for a PDF file
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # Assert that the response includes the necessary headers for
        # downloading
        fileName = '{}_trial.pdf'.format(fieldTrial.code)
        self.assertEqual(
            response['Content-Disposition'],
            'attachment; filename="{}"'.format(fileName)
        )

        # Add filetrial
        helper = TrialHelper(root_path='./baaswebapp/tests/fixtures/')
        helper.uploadTrialFile(
            fieldTrial,
            './baaswebapp/tests/fixtures/input/dummy.txt')
        expectFolder = './baaswebapp/tests/fixtures/trials/{}/'.format(
            fieldTrial.code)
        expectFile = ''.join([expectFolder, 'dummy.txt'])
        self.assertTrue(os.path.exists(expectFile))
        self.assertEqual(fieldTrial.report_filename,
                         '{}/dummy.txt'.format(fieldTrial.code))
        os.remove(expectFile)
        os.rmdir(expectFolder)

        request = self._apiFactory.get('fieldtrial_api')
        self._apiFactory.setUser(request)
        apiView = FieldTrialApi()
        response = apiView.get(request,
                               field_trial_id=fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'field trial')

        deleteRequest = self._apiFactory.delete('fieldtrial-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = fieldTrial.id
        response = FieldTrialDeleteView.as_view()(deleteRequest,
                                                  pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FieldTrial.objects.filter(pk=deletedId).exists())
