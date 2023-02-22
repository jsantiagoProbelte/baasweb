from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, ProductThesis,\
     Thesis, Evaluation, TrialAssessmentSet, AssessmentType, AssessmentUnit,\
     Replica
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.data_models import ThesisData, ReplicaData
from trialapp.assessment_views import\
    AssessmentUpdateView, AssessmentCreateView,\
    AssessmentApi, AssessmentListView, AssessmentDeleteView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class EvaluationViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            Thesis.create_Thesis(**thesis)
        for productThesis in TrialAppModelTest.PRODUCT_THESIS:
            ProductThesis.create_ProductThesis(**productThesis)
        self._units = [TrialAssessmentSet.objects.create(
            field_trial=self._fieldTrial,
            type=AssessmentType.objects.get(pk=i),
            unit=AssessmentUnit.objects.get(pk=i)) for i in range(1, 3)]

    def test_evaluation_emply_list(self):
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
        evaluationData = TrialAppModelTest.EVALUATION[0]
        request = self._apiFactory.post('assessment-add',
                                        data=evaluationData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        evaluation = Evaluation.objects.get(name=evaluationData['name'])
        self.assertEqual(evaluation.name, evaluationData['name'])
        self.assertEqual(response.status_code, 302)
        # TODO: self.assertContains(response, evaluation.evaluation_date)

        # Editar y ver nuevo
        request = self._apiFactory.get(
            'assessment-update', args=[evaluation.id])
        self._apiFactory.setUser(request)
        response = AssessmentUpdateView.as_view()(
            request,
            pk=evaluation.id)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, evaluationData['name'])
        self.assertEqual(response.status_code, 200)

        newName = 'otro name'
        evaluationData['name'] = newName
        requestPost = self._apiFactory.post(
            'assessment-update', data=evaluationData)
        self._apiFactory.setUser(requestPost)
        response = AssessmentUpdateView.as_view()(
            requestPost, pk=evaluation.id)
        self.assertEqual(response.status_code, 302)
        # TO DO: self.assertContains(response, evaluation.getTitle())

    def test_AssessmentApi(self):
        # Creating thesis , but not with all attributres
        itemData = TrialAppModelTest.EVALUATION[0]
        request = self._apiFactory.post('assessment-add', itemData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Evaluation.objects.get(name=itemData['name'])

        getRequest = self._apiFactory.get('thesis_api')
        apiView = AssessmentApi()
        response = apiView.get(getRequest,
                               **{'evaluation_id': item.id})
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
        self.assertFalse(Evaluation.objects.filter(pk=deletedId).exists())

    def test_AssessmentApiGetData(self):
        evaluationData = TrialAppModelTest.EVALUATION[0]
        request = self._apiFactory.post('evaluation-add',
                                        data=evaluationData)
        self._apiFactory.setUser(request)
        response = AssessmentCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Evaluation.objects.get(name=evaluationData['name'])
        self.assertEqual(item.getName(), '66-BBCH')

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'evaluation_id': item.id})
        self.assertEqual(response.status_code, 200)
        # No data, it enables samples views
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-sample-tab"')

        # Lets add data on thesis
        for thesis in Thesis.getObjects(self._fieldTrial):
            ThesisData.objects.create(
                value=66, reference=thesis,
                unit=self._units[0], evaluation=item)

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'evaluation_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-thesis-tab"')

        # Lets add some replica data to test we have replica view activated
        Replica.createReplicas(thesis, 4)
        for replica in Replica.getObjects(thesis):
            ReplicaData.objects.create(
                value=66, reference=replica,
                unit=self._units[0], evaluation=item)

        apiView = AssessmentApi()
        getRequest = self._apiFactory.get('assessment_api')
        response = apiView.get(getRequest,
                               **{'evaluation_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '"nav-link active" id="v-pills-replica-tab"')

        # if we go to evaluation list, we show thesis as active
        request = self._apiFactory.get('assessment-list')
        self._apiFactory.setUser(request)
        response = AssessmentListView.as_view()(
            request, **{'field_trial_id': self._fieldTrial.id})
        self.assertNotContains(response, 'No assessments yet.')
        self.assertContains(response, 'show active" id="v-pills-thesis"')
