from django.test import TestCase
from trialapp.models import Product, FieldTrial, TrialDbInitialLoader
from catalogue.product_views import ProductListView, ProductApi
from baaswebapp.tests.test_views import ApiRequestHelperTest


class ProductViewsTest(TestCase):

    _apiFactory = None

    FIELDTRIALS = [{
        'name': 'fieldTrial 666',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 1,
        'project': 1,
        'crop': 1,
        'plague': 1,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3},
        {
        'name': 'fieldTrial 999',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 1,
        'project': 1,
        'crop': 2,
        'plague': 2,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3},
        {
        'name': 'fieldTrial 333',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 2,
        'project': 1,
        'crop': 1,
        'plague': 2,
        'initiation_date': '2021-07-01',
        'contact': 'Mr Farmer',
        'location': 'La Finca',
        'replicas_per_thesis': 4,
        'report_filename': '',
        'blocks': 3},
    ]
    _products = []
    _fieldTrials = []

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        for fieldTrialInfo in ProductViewsTest.FIELDTRIALS:
            self._fieldTrials.append(
                FieldTrial.create_fieldTrial(**fieldTrialInfo))

        # TrialAssessmentSet.objects.create(
        #     field_trial=product,
        #     type=AssessmentType.objects.get(pk=1),
        #     unit=AssessmentUnit.objects.get(pk=1))

    def test_trialapp_index(self):
        request = self._apiFactory.get('product-list')
        self._apiFactory.setUser(request)
        response = ProductListView.as_view()(request)

        request = self._apiFactory.get('product-list')
        self._apiFactory.setUser(request)
        response = ProductListView.as_view()(request)
        self.assertNotContains(response, 'No Product yet.')
        numberProducts = Product.objects.count()
        self.assertContains(
            response,
            '({}) Products'.format(numberProducts))
        products = Product.objects.all()
        for product in products:
            self.assertContains(response, product.name)

    def test_showProduct(self):
        productid=4
        product = Product.objects.get(pk=productid)
        request = self._apiFactory.get(
            'product_api',
            data={'product_id': productid})
        self._apiFactory.setUser(request)
        apiView = ProductApi()
        response = apiView.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)

        deletedId = productid
        deleteData = {'item_id': deletedId}
        deleteRequest = self._apiFactory.post(
            'product_api',
            data=deleteData)
        self._apiFactory.setUser(deleteRequest)

        response = apiView.delete(deleteRequest)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Product.objects.filter(pk=deletedId).exists())
