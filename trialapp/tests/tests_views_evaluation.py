from django.test import TestCase
from trialapp.models import FieldTrial, ProductEvaluation, ProductThesis,\
     Thesis, TrialDbInitialLoader, Evaluation
from trialapp.tests.tests_models import TrialAppModelTest

from trialapp.evaluation_views import editEvaluation, saveEvaluation,\
    ManageProductToEvaluation, AssessmentApi, EvaluationListView
# from trialapp.evaluation_views import editEvaluation
from baaswebapp.tests.test_views import ApiRequestHelperTest


class EvaluationViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        FieldTrial.create_fieldTrial(**TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            Thesis.create_Thesis(**thesis)
        for productThesis in TrialAppModelTest.PRODUCT_THESIS:
            ProductThesis.create_ProductThesis(**productThesis)

    def test_evaluation_emply_list(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])

        request = self._apiFactory.get(
            'evaluation-list',
            data={'field_trial_id': fieldTrial.id})
        self._apiFactory.setUser(request)
        response = EvaluationListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'assessments')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'No assessments yet.')

    def test_editfieldtrial(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        request = self._apiFactory.get('/edit_evaluation')
        self._apiFactory.setUser(request)
        response = editEvaluation(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-evaluation')
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        evaluationData = TrialAppModelTest.APPLICATION[0]
        request = self._apiFactory.post('evaluation-save',
                                        data=evaluationData)
        self._apiFactory.setUser(request)
        response = saveEvaluation(request)
        evaluation = Evaluation.objects.get(name=evaluationData['name'])
        self.assertEqual(evaluation.name, evaluationData['name'])
        self.assertEqual(response.status_code, 302)

        # We should get some productevaluation for free
        # We should have as many as product in thesis
        productsThesis = ProductThesis.getObjectsPerFieldTrial(fieldTrial)
        productsEvaluation = ProductEvaluation.getObjects(evaluation)
        self.assertGreater(len(productsThesis), 0)
        totalProductApp = len(productsEvaluation)
        self.assertEqual(len(productsThesis), totalProductApp)

        # Editar y ver nuevo
        request = self._apiFactory.get(
            '/edit_evaluation/{}'.format(fieldTrial.id))
        self._apiFactory.setUser(request)
        response = editEvaluation(
            request,
            field_trial_id=fieldTrial.id,
            evaluation_id=evaluation.id)
        self.assertContains(response, 'create-evaluation')
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, evaluationData['name'])
        self.assertEqual(response.status_code, 200)

        evaluationData['evaluation_id'] = evaluation.id
        request = self._apiFactory.post('evaluation-save',
                                        data=evaluationData)
        self._apiFactory.setUser(request)
        response = saveEvaluation(request)
        evaluation2 = Evaluation.objects.get(name=evaluation.name)
        self.assertEqual(response.status_code, 302)

        # Lets delete some products
        deleteData = {'item_id': productsEvaluation[0].id}
        deleteProductEvaluationRequest = self._apiFactory.post(
            'manage_product_to_evaluation_api',
            data=deleteData)
        apiView = ManageProductToEvaluation()
        response = apiView.delete(deleteProductEvaluationRequest)
        self._apiFactory.setUser(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductEvaluation.objects.count(),
                         totalProductApp-1)

        # lets add it again
        productData = {'product': productsThesis[0].id,
                       'evaluation_id': evaluation2.id}
        addProductEvaluationRequest = self._apiFactory.post(
            '/manage_product_to_evaluation_api',
            data=productData)
        response = apiView.post(addProductEvaluationRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductEvaluation.objects.count(),
                         totalProductApp)

    def test_AssessmentApi(self):
        evaluationData = TrialAppModelTest.APPLICATION[0]
        request = self._apiFactory.post('evaluation-save',
                                        data=evaluationData)
        self._apiFactory.setUser(request)
        response = saveEvaluation(request)
        item = Evaluation.objects.get(name=evaluationData['name'])
        self.assertEqual(item.getName(), '66-BBCH')
        deletedId = item.id
        deleteData = {'item_id': deletedId}
        deleteRequest = self._apiFactory.post(
            'thesis_api',
            data=deleteData)
        apiView = AssessmentApi()
        response = apiView.delete(deleteRequest)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Evaluation.objects.filter(pk=deletedId).exists())
