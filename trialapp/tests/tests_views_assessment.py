from django.test import TestCase
from baaswebapp.models import RateTypeUnit
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica
from trialapp.data_models import Assessment, ThesisData, ReplicaData
from baaswebapp.tests.tests_helpers import TrialTestData
from trialapp.assessment_views import\
    AssessmentUpdateView, AssessmentCreateView, \
    AssessmentApi, AssessmentListView, AssessmentDeleteView, \
    AssessmentView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class AssessmentViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._trial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        self._trial.latitude = '1.0'
        self._trial.longitude = '1.0'
        self._trial.save()
        for thesis in TrialTestData.THESIS:
            Thesis.createThesis(**thesis)
        self._unit = RateTypeUnit.objects.get(id=1)

    def test_assessment_emply_list(self):
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._trial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'assessments')
        self.assertContains(response, self._trial.name)
        self.assertContains(response, 'No assessments yet.')

    def test_createAssessment(self):
        request = self._apiFactory.get('assessment-add')
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request,  field_trial_id=self._trial.id)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one assessment
        assessmentData = TrialTestData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        assessment = Assessment.objects.get(name=assessmentData['name'])
        self.assertEqual(assessment.name, assessmentData['name'])
        self.assertEqual(response.status_code, 302)
        self.assertTrue('-BBCH' in assessment.getContext())
        self.assertTrue('/assessment/{}/'.format(assessment.id) ==
                        assessment.get_absolute_url())
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
        itemData = TrialTestData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add', itemData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        self.assertEqual(response.status_code, 302)
        item = Assessment.objects.get(name=itemData['name'])

        getRequest = self._apiFactory.get('thesis_api')
        self._apiFactory.setUser(getRequest)
        response = AssessmentView.as_view()(
            getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        # add weather
        TrialTestData.addWeatherData(item)

        # Let's call thesis list
        getRequest = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(getRequest)
        response = AssessmentListView.as_view()(
            getRequest, **{'field_trial_id': self._trial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        # Delete
        deleteRequest = self._apiFactory.delete('assessment-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = item.id
        response = AssessmentDeleteView.as_view()(deleteRequest,
                                                  pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Assessment.objects.filter(pk=deletedId).exists())

    def test_AssessmentApiGetData(self):
        assessmentData = TrialTestData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        self.assertEqual(response.status_code, 302)
        item = Assessment.objects.get(name=assessmentData['name'])
        self.assertEqual(item.getName(), '66-BBCH')

        getRequest = self._apiFactory.get('assessment')
        self._apiFactory.setUser(getRequest)
        response = AssessmentView.as_view()(
            getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)
        # No data, it enables samples views

        # Lets add data on thesis
        for thesis in Thesis.getObjects(self._trial):
            ThesisData.objects.create(
                value=66, reference=thesis, assessment=item)

        getRequest = self._apiFactory.get('assessment_api')
        self._apiFactory.setUser(getRequest)
        response = AssessmentView.as_view()(
            getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)

        # Lets add some replica data to test we have replica view activated
        Replica.createReplicas(thesis, 4)
        for replica in Replica.getObjects(thesis):
            ReplicaData.objects.create(
                value=66, reference=replica, assessment=item)

        getRequest = self._apiFactory.get('assessment_api')
        self._apiFactory.setUser(getRequest)
        response = AssessmentView.as_view()(
            getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)

        # if we go to assessment list, we show thesis as active
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._trial.id})
        self.assertNotContains(response, 'No assessments yet.')

    def test_AssessmentApiPostData(self):
        assessmentData = TrialTestData.ASSESSMENT[0].copy()
        assessmentData['rate_type'] = RateTypeUnit.objects.get(
            id=assessmentData['rate_type'])
        ass = Assessment.objects.create(**assessmentData)

        newName = 'new data'
        requestPost = self._apiFactory.post(
            'assessment_api',
            data={'data_point_id': 'whatever-{}'.format(ass.id),
                  'name': newName})
        self._apiFactory.setUser(requestPost)
        AssessmentApi.as_view()(requestPost)
        ass1 = Assessment.objects.get(id=ass.id)
        self.assertEqual(ass1.name, newName)

        part_rated = 'new part'
        requestPost = self._apiFactory.post(
            'assessment_api',
            data={'data_point_id': 'whatever-{}'.format(ass.id),
                  'part_rated': part_rated})
        self._apiFactory.setUser(requestPost)
        AssessmentApi.as_view()(requestPost)
        ass1 = Assessment.objects.get(id=ass.id)
        self.assertEqual(ass1.part_rated, part_rated)

        crop_stage_majority = 'new bbch'
        requestPost = self._apiFactory.post(
            'assessment_api',
            data={'data_point_id': 'whatever-{}'.format(ass.id),
                  'crop_stage_majority': crop_stage_majority})
        self._apiFactory.setUser(requestPost)
        AssessmentApi.as_view()(requestPost)
        ass1 = Assessment.objects.get(id=ass.id)
        self.assertEqual(ass1.crop_stage_majority, crop_stage_majority)

        rate_type = 1
        requestPost = self._apiFactory.post(
            'assessment_api',
            data={'data_point_id': 'whatever-{}'.format(ass.id),
                  'rate_type': rate_type})
        self._apiFactory.setUser(requestPost)
        AssessmentApi.as_view()(requestPost)
        ass1 = Assessment.objects.get(id=ass.id)
        self.assertEqual(ass1.rate_type.id, rate_type)

        assessment_date = '2022-09-01'
        requestPost = self._apiFactory.post(
            'assessment_api',
            data={'data_point_id': 'whatever-{}'.format(ass.id),
                  'assessment_date': assessment_date})
        self._apiFactory.setUser(requestPost)
        AssessmentApi.as_view()(requestPost)
        ass1 = Assessment.objects.get(id=ass.id)
        self.assertEqual(ass1.assessment_date.isoformat(),
                         assessment_date)
