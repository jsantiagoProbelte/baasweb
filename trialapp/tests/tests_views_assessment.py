from django.test import TestCase
from baaswebapp.models import RateTypeUnit, Weather
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica
from trialapp.data_models import Assessment, ThesisData, ReplicaData
from trialapp.tests.tests_helpers import TrialAppModelData
from trialapp.assessment_views import\
    AssessmentUpdateView, AssessmentCreateView, \
    AssessmentApi, AssessmentListView, AssessmentDeleteView, \
    AssessmentView
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.trial_views import trialContentApi, TrialContent


class AssessmentViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelData.FIELDTRIALS[0])
        self._fieldTrial.latitude = '1.0'
        self._fieldTrial.longitude = '1.0'
        self._fieldTrial.save()
        for thesis in TrialAppModelData.THESIS:
            Thesis.create_Thesis(**thesis)
        self._unit = RateTypeUnit.objects.get(id=1)

    def addWeatherData(self, ass):
        Weather.objects.create(
            date=ass.assessment_date,
            recent=False,
            latitude=float(ass.field_trial.latitude),
            longitude=float(ass.field_trial.longitude),
            max_temp=30.0,
            min_temp=15.0,
            mean_temp=20.0,
            soil_temp_0_to_7cm=10.0,
            soil_temp_7_to_28cm=10.0,
            soil_temp_28_to_100cm=10.0,
            soil_temp_100_to_255cm=10.0,
            soil_moist_0_to_7cm=10.0,
            soil_moist_7_to_28cm=10.0,
            soil_moist_28_to_100cm=10.0,
            soil_moist_100_to_255cm=10.0,
            dew_point=10.0,
            relative_humidity=10.0,
            precipitation=10.0,
            precipitation_hours=10.0,
            max_wind_speed=10.0)

    def test_assessment_emply_list(self):
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._fieldTrial.id})
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
        assessmentData = TrialAppModelData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
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
        itemData = TrialAppModelData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add', itemData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Assessment.objects.get(name=itemData['name'])

        getRequest = self._apiFactory.get('thesis_api')
        self._apiFactory.setUser(getRequest)
        response = AssessmentView.as_view()(
            getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        # add weather
        self.addWeatherData(item)

        # Let's call thesis list
        getRequest = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(getRequest)
        response = AssessmentListView.as_view()(
            getRequest, **{'field_trial_id': self._fieldTrial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        # Try with the trialContentApi
        for content in list(TrialContent.FETCH_FUNCTIONS.keys()):
            data = {'id': self._fieldTrial.id,
                    'content_type': content}
            getRequest = self._apiFactory.get('trial_content',
                                              data=data)
            self._apiFactory.setUser(getRequest)
            response = trialContentApi(getRequest)
            self.assertEqual(response.status_code, 200)

        # Delete
        deleteRequest = self._apiFactory.delete('assessment-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = item.id
        response = AssessmentDeleteView.as_view()(deleteRequest,
                                                  pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Assessment.objects.filter(pk=deletedId).exists())

    def test_AssessmentApiGetData(self):
        assessmentData = TrialAppModelData.ASSESSMENT[0]
        request = self._apiFactory.post('assessment-add',
                                        data=assessmentData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
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
        for thesis in Thesis.getObjects(self._fieldTrial):
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
            request, **{'field_trial_id': self._fieldTrial.id})
        self.assertNotContains(response, 'No assessments yet.')

    def test_AssessmentApiPostData(self):
        assessmentData = TrialAppModelData.ASSESSMENT[0].copy()
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
