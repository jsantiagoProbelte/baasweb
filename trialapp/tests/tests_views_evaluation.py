from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, ProductEvaluation, ProductThesis,\
     Thesis, TrialDbInitialLoader, Evaluation
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory

from trialapp.evaluation_views import editEvaluation, saveEvaluation,\
    ManageProductToEvaluation
# from trialapp.evaluation_views import editEvaluation


class EvaluationViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        FieldTrial.create_fieldTrial(**TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            Thesis.create_Thesis(**thesis)
        for productThesis in TrialAppModelTest.PRODUCT_THESIS:
            ProductThesis.create_ProductThesis(**productThesis)

    def test_evaluation_emply_list(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        response = self.client.get(reverse(
            'evaluation-list', args=[fieldTrial.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'assessments')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'No assessments yet.')

    def test_editfieldtrial(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        request_factory = RequestFactory()
        request = request_factory.get('/edit_evaluation')
        response = editEvaluation(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-evaluation')
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        evaluationData = TrialAppModelTest.APPLICATION[0]
        request = request_factory.post('evaluation-save',
                                       data=evaluationData)
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
        request = request_factory.get(
            '/edit_evaluation/{}'.format(fieldTrial.id))
        response = editEvaluation(
            request,
            field_trial_id=fieldTrial.id,
            evaluation_id=evaluation.id)
        self.assertContains(response, 'create-evaluation')
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, evaluationData['name'])
        self.assertEqual(response.status_code, 200)

        newscale = 'new name'
        evaluationData['evaluation_id'] = evaluation.id
        evaluationData['crop_stage_scale'] = newscale
        request = request_factory.post('evaluation-save',
                                       data=evaluationData)
        response = saveEvaluation(request)
        evaluation2 = Evaluation.objects.get(name=evaluation.name)
        self.assertEqual(evaluation2.crop_stage_scale, newscale)
        self.assertEqual(response.status_code, 302)

        # Lets delete some products
        deleteData = {'item_id': productsEvaluation[0].id}
        deleteProductEvaluationRequest = request_factory.post(
            'manage_product_to_evaluation_api',
            data=deleteData)
        apiView = ManageProductToEvaluation()
        response = apiView.delete(deleteProductEvaluationRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductEvaluation.objects.count(),
                         totalProductApp-1)

        # lets add it again
        productData = {'product': productsThesis[0].id,
                       'evaluation_id': evaluation2.id}
        addProductEvaluationRequest = request_factory.post(
            '/manage_product_to_evaluation_api',
            data=productData)
        response = apiView.post(addProductEvaluationRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductEvaluation.objects.count(),
                         totalProductApp)
