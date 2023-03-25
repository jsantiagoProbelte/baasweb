from django.test import TestCase
from baaswebapp.models import RateTypeUnit
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica
from trialapp.data_models import Assessment, ThesisData, ReplicaData
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.assessment_views import\
    AssessmentUpdateView, AssessmentCreateView,\
    AssessmentApi, AssessmentListView, AssessmentDeleteView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class AssessmentViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            Thesis.create_Thesis(**thesis)
        self._unit = RateTypeUnit.objects.get(id=1)

    def test_assessment_emply_list(self):
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._fieldTrial.id})
        self.assertContains(response, 'show active" id="v-pills-replica"')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'assessments')
        self.assertContains(response, self._fieldTrial.name)
        self.assertContains(response, 'No assessments yet.')

    def test_createAssessment(self):
        request = self._apiFactory.get('assessment-add')
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request,  field_trial_id=self._fieldTrial.id)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one assessment
        assessmentData = TrialAppModelTest.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        assessment = Assessment.objects.get(name=assessmentData['name'])
        self.assertEqual(assessment.name, assessmentData['name'])
        self.assertEqual(response.status_code, 302)
        # TODO: self.assertContains(response, assessment.assessment_date)

        # Editar y ver nuevo
        request = self._apiFactory.get(
            'assessment-update', args=[assessment.id])
        self._apiFactory.setUser(request)
        response = AssessmentUpdateView.as_view()(
            request,
            pk=assessment.id)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, assessmentData['name'])
        self.assertEqual(response.status_code, 200)

        newName = 'otro name'
        assessmentData['name'] = newName
        requestPost = self._apiFactory.post(
            'assessment-update', data=assessmentData)
        self._apiFactory.setUser(requestPost)
        response = AssessmentUpdateView.as_view()(
            requestPost, pk=assessment.id)
        self.assertEqual(response.status_code, 302)
        # TO DO: self.assertContains(response, assessment.getTitle())

    def test_AssessmentApi(self):
        # Creating thesis , but not with all attributres
        itemData = TrialAppModelTest.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add', itemData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Assessment.objects.get(name=itemData['name'])

        getRequest = self._apiFactory.get('thesis_api')
        apiView = AssessmentApi()
        response = apiView.get(getRequest,
                               **{'assessment_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        # Let's call thesis list
        getRequest = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(getRequest)
        response = AssessmentListView.as_view()(
            getRequest, **{'field_trial_id': self._fieldTrial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        deleteRequest = self._apiFactory.delete('assessment-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = item.id
        response = AssessmentDeleteView.as_view()(deleteRequest,
                                                  pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Assessment.objects.filter(pk=deletedId).exists())

    def test_AssessmentApiGetData(self):
        assessmentData = TrialAppModelTest.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Assessment.objects.get(name=assessmentData['name'])
        self.assertEqual(item.getName(), '66-BBCH')

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'assessment_id': item.id})
        self.assertEqual(response.status_code, 200)
        # No data, it enables samples views
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-sample-tab"')

        # Lets add data on thesis
        for thesis in Thesis.getObjects(self._fieldTrial):
            ThesisData.objects.create(
                value=66, reference=thesis, assessment=item)

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'assessment_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-thesis-tab"')

        # Lets add some replica data to test we have replica view activated
        Replica.createReplicas(thesis, 4)
        for replica in Replica.getObjects(thesis):
            ReplicaData.objects.create(
                value=66, reference=replica, assessment=item)

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'assessment_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-replica-tab"')

        # if we go to assessment list, we show thesis as active
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._fieldTrial.id})
        self.assertNotContains(response, 'No assessments yet.')
        self.assertContains(response, 'show active" id="v-pills-thesis"')
