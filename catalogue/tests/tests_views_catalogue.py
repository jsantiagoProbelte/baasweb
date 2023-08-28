from django.test import TestCase
from baaswebapp.models import RateTypeUnit, PType
from baaswebapp.data_loaders import TrialDbInitialLoader
from catalogue.models import Product, ProductVariant, RateUnit, \
    Batch, Treatment, DEFAULT
from trialapp.models import FieldTrial, Thesis, Replica, TreatmentThesis
from trialapp.data_models import ThesisData, ReplicaData, Assessment
from catalogue.product_views import ProductApi, \
    ProductCreateView, ProductUpdateView, ProductDeleteView, \
    ProductVariantCreateView, ProductVariantUpdateView, \
    ProductVariantDeleteView, BatchCreateView, BatchUpdateView, \
    BatchDeleteView, TreatmentCreateView, TreatmentUpdateView, \
    TreatmentDeleteView, TreatmentApi, BatchApi, \
    ProductVariantApi
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.filter_helpers import ProductListView
from django.utils.translation import gettext_lazy as _


class ProductViewsTest(TestCase):

    _apiFactory = None

    FIELDTRIALS = [{
        'name': 'fieldTrial 666',
        'trial_type': 1,
        'trial_status': 1,
        'objective': 1,
        'responsible': 'Waldo',
        'product': 1,
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
    _assessments = []
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

        rateTypes = RateTypeUnit.objects.all()
        self._units = [rateTypes[i] for i in range(1, 4)]

        self._assessments = [Assessment.objects.create(
            name='eval{}'.format(i),
            assessment_date='2023-0{}-15'.format(i),
            rate_type=self._units[0],
            field_trial=self._fieldTrials[0],
            crop_stage_majority=65+i) for i in range(1, 3)]

    def test_catalogue_index(self):
        request = self._apiFactory.get('product-list')
        self._apiFactory.setUser(request)
        response = ProductListView.as_view()(request)

        request = self._apiFactory.get('product-list')
        self._apiFactory.setUser(request)
        response = ProductListView.as_view()(request)
        self.assertNotContains(response, 'No Product yet.')
        numberProducts = Product.objects.count()
        self.assertTrue(
            response,
            'analytics</span> {}</p>'.format(numberProducts))
        products = Product.objects.all()
        for product in products:
            self.assertContains(response, product.name)

    def test_showProductS_simple(self):
        productid = 4
        product = Product.objects.get(pk=productid)
        request = self._apiFactory.get('product_api')
        self._apiFactory.setUser(request)
        apiView = ProductApi()
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)

        deleteRequest = self._apiFactory.get('product-delete')
        self._apiFactory.setUser(deleteRequest)
        response = ProductDeleteView.as_view()(deleteRequest,
                                               pk=product.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, product.name)
        # TODO. It should show the product but is showing {{item.name}}
        # # This works with get
        self.assertContains(
            response,
            _('Are you sure to delete'))

        # Now let's post and really delete
        deleteRequest = self._apiFactory.delete('product-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = product.id
        response = ProductDeleteView.as_view()(deleteRequest,
                                               pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=deletedId).exists())

    def test_showProductS_graph(self):
        productid = 1

        # Le's add data
        value = 1000.10
        self.assertEqual(ThesisData.objects.count(), 0)
        for thesis in self._theses:
            for assessment in self._assessments:
                for unit in self._units:
                    ThesisData.objects.create(
                        value=value,
                        assessment=assessment,
                        reference=thesis)
                    value += 500.10

        levelId = 'level-thesis'
        request = self._apiFactory.get(
            'product_api',
            data={'show_data': 'show_data',
                  'crops': self._fieldTrials[0].crop.id,
                  'plagues': self._fieldTrials[0].plague.id,
                  ProductApi.TAG_LEVEL: 'thesis',
                  ProductApi.TAG_DIMENSIONS: self._units[0].id})
        self._apiFactory.setUser(request)

        apiView = ProductApi()
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No data found')

        # Not enough dimensions
        request = self._apiFactory.get(
            'product_api',
            data={'show_data': 'show_data',
                  'plagues': self._fieldTrials[0].plague.id,
                  'dimensions': self._units[0].id})
        self._apiFactory.setUser(request)
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, 'Please select crop')

        # Not enough crops
        request = self._apiFactory.get(
            'product_api',
            data={'show_data': 'show_data',
                  'crops': self._fieldTrials[0].crop.id,
                  'plague': self._fieldTrials[0].plague.id,
                  levelId: levelId})
        self._apiFactory.setUser(request)
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Please select dimensions')

    def test_editProduct(self):
        data = {'name': 'New Product', 'vendor': 1,
                'biological': True,
                'type_product': PType.FUNGICIDE}
        request = self._apiFactory.post(
            'product-add',
            data=data)
        self._apiFactory.setUser(request)
        response = ProductCreateView.as_view()(request)
        self.assertTrue(response.status_code, 302)
        newProduct = Product.objects.get(name='New Product')
        self.assertEqual(newProduct.name, 'New Product')

        productOne = Product.objects.get(pk=1)
        newName = 'New Name'
        self.assertFalse(productOne.name == newName)
        requestPost = self._apiFactory.post(
            'product-update',
            data={'name': newName})
        self._apiFactory.setUser(requestPost)
        response = ProductUpdateView.as_view()(requestPost,
                                               pk=productOne.id)
        self.assertTrue(response.status_code, 302)
        self.assertContains(response, newName)

    def test_showProduct_Replica_graph(self):
        productid = 1
        request = self._apiFactory.get(
            'product_api',
            data={'show_data': 'show_data',
                  'crops': self._fieldTrials[0].crop.id,
                  'plagues': self._fieldTrials[0].plague.id,
                  'dimensions': self._units[0].id})
        self._apiFactory.setUser(request)

        apiView = ProductApi()
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No data found', count=0)
        self.assertEqual(ReplicaData.objects.count(), 0)

        # Le's add data
        value = 1000.10
        Replica.createReplicas(self._theses[0], 4)
        for replica in Replica.getObjects(self._theses[0]):
            for assessment in self._assessments:
                for unit in self._units:
                    ReplicaData.objects.create(
                        value=value,
                        assessment=assessment,
                        reference=replica)
                    value += 500.10
        response = apiView.get(request,
                               **{'product_id': productid})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No data found', count=0)

    def alltogether(self, theClass, data, reference,
                    token, modelApi,
                    createView, updateView, deleteView):
        url_model = token+'-api'
        url_add = token+'-add'
        url_update = token+'-update'
        url_delete = token+'-delete'
        createGet = self._apiFactory.get(url_add, data=data)
        self._apiFactory.setUser(createGet)
        response = createView.as_view()(createGet,
                                        reference_id=reference.id)
        self.assertTrue(response.status_code, 200)

        createPost = self._apiFactory.post(url_add, data=data)
        self._apiFactory.setUser(createPost)
        response = createView.as_view()(createPost,
                                        reference_id=reference.id)
        self.assertTrue(response.status_code, 302)
        theItem = theClass.objects.get(name=data['name'])

        if theClass == Product:
            # Check the default creation of variant and bach
            variants = ProductVariant.getItems(theItem)
            self.assertTrue(len(variants) == 1)
            self.assertTrue(DEFAULT in variants[0].name)
            batches = Batch.getItems(theItem)
            self.assertTrue(len(batches) == 1)
            self.assertTrue(DEFAULT in batches[0].name)

        if theClass == ProductVariant:
            # Check the default creation of variant and bach
            items = Batch.objects.filter(product_variant=theItem)
            self.assertTrue(len(items) == 1)
            self.assertTrue(DEFAULT in items[0].name)

        if theClass == Treatment:
            # Create a thesis and associated with this treatment
            aThesis = self._theses[0]
            TreatmentThesis.objects.create(thesis=aThesis,
                                           treatment=theItem)

        modelGet = self._apiFactory.get(url_model)
        self._apiFactory.setUser(modelGet)
        response = modelApi.as_view()(modelGet,
                                      pk=theItem.id)
        self.assertTrue(response.status_code, 200)
        self.assertContains(response, theItem.name)

        updateGet = self._apiFactory.get(url_update)
        self._apiFactory.setUser(updateGet)
        response = updateView.as_view()(updateGet,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 200)

        newName = 'newName'
        updatePost = self._apiFactory.post(url_update, data={'name': newName})
        self._apiFactory.setUser(updatePost)
        response = updateView.as_view()(updatePost,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 302)
        self.assertTrue(theClass.objects.get(id=theItem.id).name,
                        newName)

        deleteGet = self._apiFactory.get(url_delete)
        self._apiFactory.setUser(deleteGet)
        response = deleteView.as_view()(deleteGet,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 200)
        self.assertTrue(theClass.objects.filter(id=theItem.id).exists())

        deletePost = self._apiFactory.post(url_delete)
        self._apiFactory.setUser(deletePost)
        response = deleteView.as_view()(deletePost,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 302)
        self.assertFalse(theClass.objects.filter(id=theItem.id).exists())

    def test_ProductVariant(self):
        product = Product.objects.create(name='A product')
        data = {'name': 'vvvvv', 'description': 'description'}
        self.alltogether(
            ProductVariant, data, product, 'product_variant',
            ProductVariantApi,
            ProductVariantCreateView, ProductVariantUpdateView,
            ProductVariantDeleteView)

    def test_Batch(self):
        product = Product.objects.create(name='A product')
        variant = ProductVariant.objects.create(name='A variant',
                                                product=product)
        rateUnit = RateUnit.objects.create(name='unit')
        data = {'name': 'bbbbbb', 'serial_number': 'serial_number', 'rate': 1,
                'rate_unit': rateUnit.id}
        self.alltogether(
            Batch, data, variant, 'batch', BatchApi,
            BatchCreateView, BatchUpdateView, BatchDeleteView)

        cdata = {'name': 'bbbbbb', 'serial_number': 'serial_number', 'rate': 1,
                 'rate_unit_id': rateUnit.id, 'product_variant_id': variant.id}
        created = Batch.objects.create(**cdata)
        items = Batch.getItems(product)
        self.assertTrue(len(items) > 0)

        for item in items:
            if item.id == created.id:
                self.assertEqual(item.name,
                                 created.name)
                self.assertTrue('batch' in
                                created.get_absolute_url())

    def test_Treatment(self):
        product = Product.objects.create(name='A product')
        variant = ProductVariant.objects.create(name='A variant',
                                                product=product)
        rateUnit = RateUnit.objects.create(name='unit')
        batch = Batch.objects.create(
            **{'name': 'bbbbbbb', 'serial_number': 'sn', 'rate': 1,
               'rate_unit': rateUnit, 'product_variant': variant})
        data = {"name": 'pppp', 'rate': 1, 'rate_unit': rateUnit.id}

        self.alltogether(
            Treatment, data, batch, 'treatment', TreatmentApi,
            TreatmentCreateView, TreatmentUpdateView, TreatmentDeleteView)

        cdata = {"name": 'pppp', 'rate': 1, 'rate_unit_id': rateUnit.id,
                 'batch_id': batch.id}
        treatment = Treatment.objects.create(**cdata)
        treatments = Treatment.getItems(product)
        self.assertTrue(len(treatments) > 0)

        displays = Treatment.displayItems(product)
        self.assertEqual(len(treatments), len(displays))

        for item in displays:
            for treatment in treatments:
                if treatment.id == item['id']:
                    self.assertEqual(item['name'],
                                     treatment.getName())
                    self.assertTrue('treatment' in
                                    treatment.get_absolute_url())

        cdata = {"name": '', 'rate': 1, 'rate_unit_id': rateUnit.id,
                 'batch_id': batch.id}
        treatment2 = Treatment.objects.create(**cdata)
        self.assertTrue(product.name in treatment2.getName())
        self.assertFalse(product.name in treatment2.getName(short=True))

    def test_ProductApi(self):
        product = Product.objects.create(name='A product')
        variant = ProductVariant.objects.create(name='A variant',
                                                product=product)
        rateUnit = RateUnit.objects.create(name='unit')
        batch = Batch.objects.create(
            **{'name': 'bbbbbbb', 'serial_number': 'sn', 'rate': 1,
               'rate_unit': rateUnit, 'product_variant': variant})
        cdata = {"name": 'pppp', 'rate': 1, 'rate_unit_id': rateUnit.id,
                 'batch_id': batch.id}
        Treatment.objects.create(**cdata)

        # ProductApi
        api = ProductApi()
        tree = api.getProductTree(product)
        self.assertTrue(tree[0]['name'] == variant.name)
        self.assertTrue('batches' in tree[0])
