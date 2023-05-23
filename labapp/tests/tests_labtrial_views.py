from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial
from trialapp.tests.tests_models import TrialAppModelTest
from labapp.labtrial_views import LabTrialView, DataLabHelper
from labapp.models import LabDataPoint, LabAssessment, LabThesis
from labapp.labtrial_views import LabTrialCreateView,\
    LabTrialUpdateView, LabTrialListView, SetLabDataPoint,\
    SetLabThesis


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

        labTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        labTrial.trial_meta = FieldTrial.TrialMeta.LAB_TRIAL
        labTrial.samples_per_replica = 20
        labTrial.save()

        request = self._apiFactory.get('labtrial-list')
        self._apiFactory.setUser(request)
        response = LabTrialListView.as_view()(request)
        self.assertNotContains(response, 'No Trials yet.')
        self.assertContains(response, labTrial.name)
        labTrial.delete()

    def test_createLabTrial(self):
        request = self._apiFactory.get('labtrial-add')
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        labTrialData = TrialAppModelTest.FIELDTRIALS[0].copy()
        labTrialData['samples_per_replica'] = 24
        request = self._apiFactory.post(
            'labtrial-add', data=labTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        # it is missing a code.
        labTrialData['code'] = '19701409'
        request = self._apiFactory.post(
            'labtrial-add', data=labTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialCreateView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        labTrial = FieldTrial.objects.get(name=labTrialData['name'])
        self.assertEqual(labTrial.name, labTrialData['name'])
        self.assertTrue(labTrial.code is not None)

        request = self._apiFactory.get('labtrial-update')
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=labTrial.id)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        labTrialData['responsible'] = newresponsible

        request = self._apiFactory.post(
            'labtrial-update', data=labTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=labTrial.id)
        labTrial = FieldTrial.objects.get(name=labTrialData['name'])
        self.assertEqual(labTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

        labTrialData['samples_per_replica'] = '3'
        self.assertEqual(labTrial.samples_per_replica, 24)
        request = self._apiFactory.post(
            'labtrial-update', data=labTrialData)
        self._apiFactory.setUser(request)
        response = LabTrialUpdateView.as_view()(
            request, pk=labTrial.id)
        labTrial = FieldTrial.objects.get(name=labTrialData['name'])
        self.assertEqual(labTrial.samples_per_replica, 3)
        self.assertEqual(response.status_code, 302)

        request = self._apiFactory.get('labtrial-show')
        self._apiFactory.setUser(request)
        apiView = LabTrialView()
        response = apiView.get(request,
                               pk=labTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, labTrial.name)
        self.assertContains(response, 'lab trial')

        # Let's add data
        assessment = LabAssessment.objects.get(trial=labTrial)
        points = LabDataPoint.getDataPointsAssessment(assessment)
        dataHelper = DataLabHelper(labTrial)
        self.assertTrue(len(points) > 0)
        thePointId = points[0].id
        addData = {'data_point_id': dataHelper.generateDataPointId(
                        DataLabHelper.T_VALUE, thePointId),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point_lab',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        apiView = SetLabDataPoint()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        thePoint = LabDataPoint.objects.get(id=thePointId)
        self.assertEqual(thePoint.value, 33)

        addData = {'data_point_id': dataHelper.generateDataPointId(
                        DataLabHelper.T_TOTAL, thePointId),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point_lab',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        thePoint = LabDataPoint.objects.get(id=thePointId)
        self.assertEqual(thePoint.total, 66)

        # Let's change a thesis name
        thesisLab = LabThesis.objects.filter(trial=labTrial)
        theThesisId = thesisLab[0].id
        addData = {'data_point_id': 'thesis-input-{}'.format(theThesisId),
                   'data-point': "OleOle"}
        addDataPoint = self._apiFactory.post(
            'set_thesis_name',
            data=addData)
        apiView = SetLabThesis()
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        theThesis = LabThesis.objects.get(id=theThesisId)
        self.assertEqual(theThesis.name, "OleOle")
