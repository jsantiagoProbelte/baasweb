from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, ProductApplication, ProductThesis, Thesis, TrialDbInitialLoader,\
    Application
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory

from trialapp.application_views import editApplication, saveApplication,\
    ManageProductToApplication
# from trialapp.application_views import editApplication


class ApplicationViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        FieldTrial.create_fieldTrial(**TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            Thesis.create_Thesis(**thesis)
        for productThesis in TrialAppModelTest.PRODUCT_THESIS:
            ProductThesis.create_ProductThesis(**productThesis)

    def test_application_emply_list(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        response = self.client.get(reverse(
            'application-list', args=[fieldTrial.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'applications')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'No applications yet.')

    def test_editfieldtrial(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        request_factory = RequestFactory()
        request = request_factory.get('/edit_application')
        response = editApplication(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-application')
        self.assertContains(response, 'New application')
        self.assertNotContains(response, 'Edit application')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        applicationData = TrialAppModelTest.APPLICATION[0]
        request = request_factory.post('application-save',
                                       data=applicationData)
        response = saveApplication(request)
        application = Application.objects.get(name=applicationData['name'])
        self.assertEqual(application.name, applicationData['name'])
        self.assertEqual(response.status_code, 302)

        # We should get some productapplication for free
        # We should have as many as product in thesis
        productsThesis = ProductThesis.getObjectsPerFieldTrial(fieldTrial)
        productsApplication = ProductApplication.getObjects(application)
        self.assertGreater(len(productsThesis), 0)
        totalProductApp = len(productsApplication)
        self.assertEqual(len(productsThesis), totalProductApp)

        # Editar y ver nuevo
        request = request_factory.get(
            '/edit_application/{}'.format(fieldTrial.id))
        response = editApplication(
            request,
            field_trial_id=fieldTrial.id,
            application_id=application.id)
        self.assertContains(response, 'create-application')
        self.assertNotContains(response, 'New application')
        self.assertContains(response, 'Edit application')
        self.assertContains(response, applicationData['name'])
        self.assertEqual(response.status_code, 200)

        newscale = 'new name'
        applicationData['application_id'] = application.id
        applicationData['crop_stage_scale'] = newscale
        request = request_factory.post('application-save',
                                       data=applicationData)
        response = saveApplication(request)
        application2 = Application.objects.get(name=application.name)
        self.assertEqual(application2.crop_stage_scale, newscale)
        self.assertEqual(response.status_code, 302)

        # Lets delete some products
        deleteData = {'product_application_id': productsApplication[0].id}
        deleteProductApplicationRequest = request_factory.post(
            'manage_product_to_application_api',
            data=deleteData)
        apiView = ManageProductToApplication()
        response = apiView.delete(deleteProductApplicationRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductApplication.objects.count(),
                         totalProductApp-1)

        # lets add it again
        productData = {'product': productsThesis[0].id,
                       'application_id': application2.id}
        addProductApplicationRequest = request_factory.post(
            '/manage_product_to_application_api',
            data=productData)
        response = apiView.post(addProductApplicationRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductApplication.objects.count(),
                         totalProductApp)
