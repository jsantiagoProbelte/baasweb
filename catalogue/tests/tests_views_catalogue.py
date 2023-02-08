from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from catalogue.models import Product
from trialapp.models import FieldTrial,\
    Thesis, Evaluation, TrialAssessmentSet, AssessmentType,\
    AssessmentUnit
from trialapp.data_models import ThesisData
from catalogue.product_views import ProductListView, ProductApi,\
    ProductCreateView, ProductUpdateView
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.tests.tests_models import TrialAppModelTest


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
    _theses = []
    _evaluations = []
    _units = []

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        for fieldTrialInfo in ProductViewsTest.FIELDTRIALS:
            self._fieldTrials.append(
                FieldTrial.create_fieldTrial(**fieldTrialInfo))

        # for fieldTrial in self._fieldTrials:
        for thesis in TrialAppModelTest.THESIS:
            # thesis['field_trial_id'] = fieldTrial.id
            self._theses.append(Thesis.create_Thesis(**thesis))

        self._units = [TrialAssessmentSet.objects.create(
            field_trial=self._fieldTrials[0],
            type=AssessmentType.objects.get(pk=i),
            unit=AssessmentUnit.objects.get(pk=i)) for i in range(1, 3)]

        self._evaluations = [Evaluation.objects.create(
            name='eval{}'.format(i),
            evaluation_date='2023-0{}-15'.format(i),
            field_trial=self._fieldTrials[0],
            crop_stage_majority=65+i) for i in range(1, 3)]

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

    def test_showProductS_simple(self):
        productid = 4
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

    def test_showProductS_graph(self):
        productid = 1

        # Le's add data
        value = 1000.10
        self.assertEqual(ThesisData.objects.count(), 0)
        for thesis in self._theses:
            for evaluation in self._evaluations:
                for unit in self._units:
                    ThesisData.objects.create(
                        value=value,
                        evaluation=evaluation,
                        unit=unit,
                        reference=thesis)
                    value += 500.10
        cropId = 'crops-{}'.format(self._fieldTrials[0].crop.id)
        plagueId = 'plagues-{}'.format(self._fieldTrials[0].plague.id)
        dimensionId = 'dimensions-{}'.format(self._units[0].id)
        levelId = 'level-thesis'
        request = self._apiFactory.get(
            'product_api',
            data={'product_id': productid,
                  'show_data': 'show_data',
                  cropId: cropId,
                  plagueId: plagueId,
                  dimensionId: dimensionId,
                  levelId: levelId})
        self._apiFactory.setUser(request)

        apiView = ProductApi()
        response = apiView.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No data found')

    def test_editProduct(self):
        data = {'name': 'New Product', 'vendor': 1,
                'category': 1}
        request = self._apiFactory.post(
            '/product/add/',
            data=data)
        self._apiFactory.setUser(request)

        viewNew = ProductCreateView(request=request)
        viewNew.post(request)
        formNew = viewNew.get_form()
        self.assertTrue(formNew.is_valid())
        newProduct = Product.objects.filter(name='New Product')
        self.assertEqual(newProduct[0].name, 'New Product')

        productOne = Product.objects.get(pk=1)
        newName = 'New Name'
        self.assertFalse(productOne.name == newName)
        data = {'name': newName, 'vendor': 1,
                'category': 1}
        request = self._apiFactory.post(
            '/product/1/',
            data=data)
        viewNew = ProductUpdateView(request=request)
        # viewNew.post(request)
        formNew = viewNew.get_form()
        self.assertTrue(formNew.is_valid())
        newProduct = Product.objects.get(pk=1)
        # self.assertEqual(newProduct.name, newName)
