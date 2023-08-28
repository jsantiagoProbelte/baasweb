from django.test import TestCase
from baaswebapp.models import Category
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Crop, Plague
from catalogue.models import Product
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.filter_helpers import TrialFilterHelper, TrialListView, \
    CropListView, PlaguesListView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class TrialFilterTest(TestCase):
    FIRST_YEAR = 2000
    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        # Create as many as trials as assessments to try
        # different conditions
        numP = Product.objects.count()
        numC = Crop.objects.count()
        code = 1
        fakemonth = 1
        for i in range(1, numP+1):
            for j in range(1, numC+1):
                year = TrialFilterTest.FIRST_YEAR + j
                trialData = TrialAppModelTest.FIELDTRIALS[0].copy()
                trialData['name'] = f"trial{i}-{j}"
                trialData['product'] = i
                trialData['crop'] = j
                trialData['code'] = FieldTrial.formatCode(year, fakemonth,
                                                          code)
                trialData['initiation_date'] = f'{year}-07-01'
                FieldTrial.create_fieldTrial(**trialData)
                code += 1
                if code % 100 == 0:
                    code = 1
                    fakemonth += 1

    def test_emptyfilter(self):
        totalProducts = Product.objects.count()
        totalCrops = Crop.objects.count()
        totalTrials = FieldTrial.objects.count()
        self.assertEqual(totalProducts*totalCrops, totalTrials)
        for posibleEmplyFilter in [{}, {'crop': ''}]:
            fHelper = TrialFilterHelper(posibleEmplyFilter)
            fHelper.filter()
            objectList = fHelper.getClsObjects(Product)
            self.assertEqual(len(objectList), totalProducts)
            self.assertEqual(fHelper.countTrials(), totalTrials)
            # TODO test Helper.countProductCategories()
            trialsPerProduct = fHelper.countBy('product__name')
            products = list(trialsPerProduct.keys())
            self.assertEqual(len(products), totalProducts)
            self.assertEqual(trialsPerProduct[products[0]], totalCrops)
            self.assertEqual(fHelper.generateParamUrl(), '')

            productId = 1
            firstYear = TrialFilterTest.FIRST_YEAR + productId
            lastYear = TrialFilterTest.FIRST_YEAR + totalCrops
            rangeYears = f'{firstYear}-{lastYear}'
            theProduct = Product.objects.get(id=productId)
            self.assertEqual(fHelper.getMinMaxYears(
                {'product': theProduct}), rangeYears)

            counts, countProductIds = fHelper.countProductCategoriesAndCrop()
            self.assertEqual(countProductIds, totalProducts)
            self.assertEqual(len(counts), totalCrops)
            self.assertEqual(counts[1][Category.UNKNOWN],
                             totalProducts)

    def test_cropfilter(self):
        # we are going to filter for 1 crop
        # we have create 1 trial per crop and product
        expectedProducts = Product.objects.count()
        cropId = 6
        for posibleFilter in [{'crop': cropId}]:
            fHelper = TrialFilterHelper(posibleFilter)
            fHelper.filter()
            objectList = fHelper.getClsObjects(Product)
            self.assertEqual(len(objectList),
                             expectedProducts)
            self.assertEqual(fHelper.countTrials(),
                             expectedProducts)
            # TODO test Helper.countProductCategories()
            trialsPerProduct = fHelper.countBy('product__name')
            products = list(trialsPerProduct.keys())
            self.assertEqual(len(products), expectedProducts)
            self.assertEqual(trialsPerProduct[products[0]], 1)
            self.assertEqual(fHelper.generateParamUrl(),
                             f'&crop={cropId}')

            productId = 1
            firstYear = TrialFilterTest.FIRST_YEAR + cropId
            rangeYears = f'{firstYear}'
            theProduct = Product.objects.get(id=productId)
            self.assertEqual(fHelper.getMinMaxYears(
                {'product': theProduct}), rangeYears)

            # add unknown product
            otherP = Product.objects.create(name='whatever')
            self.assertEqual(fHelper.getMinMaxYears(
                {'product': otherP}), '-')

            counts, countProductIds = fHelper.countProductCategoriesAndCrop()
            self.assertEqual(countProductIds, expectedProducts)
            self.assertEqual(len(counts), 1)
            self.assertEqual(counts[cropId][Category.UNKNOWN],
                             expectedProducts)

    def test_namefilter(self):
        # we are going to filter for 1 crop
        # we have create 1 trial per crop and product
        filters = [{'name': 'trial2-3'}, {'name': '20030132'}]
        for posibleFilter in filters:
            fHelper = TrialFilterHelper(posibleFilter)
            fHelper.filter()
            objectList = fHelper.getClsObjects(Product)
            self.assertEqual(len(objectList), 1)
            self.assertEqual(fHelper.countTrials(), 1)

    def test_colors(self):
        self.assertTrue(TrialFilterHelper.colorProductType('Biofertilizer'),
                        'bg-nutritional')
        self.assertTrue(TrialFilterHelper.colorProductType('Fertilizer'),
                        'bg-nutritional')
        self.assertTrue(TrialFilterHelper.colorProductType('Bioestimulant'),
                        'bg-estimulant')
        self.assertTrue(TrialFilterHelper.colorProductType('Biocontrol'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Biofungicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Bionematicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Bioherbicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Fungicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Nematicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('Herbicide'),
                        'bg-control')
        self.assertTrue(TrialFilterHelper.colorProductType('blabla'),
                        'bg-unknown')
        self.assertTrue(TrialFilterHelper.colorProductType(None),
                        'bg-unknown')

    def listQuery(self, url, restClass, cls):
        request = self._apiFactory.get(url)
        self._apiFactory.setUser(request)
        response = restClass.as_view()(request)
        self.assertEqual(response.status_code, 200)

        items = cls.objects.all()
        return response, items

    def test_trials(self):
        response, items = self.listQuery('trials', TrialListView,
                                         FieldTrial)
        for item in items:
            self.assertContains(response, item.code)

    def test_crops(self):
        response, items = self.listQuery('crops', CropListView,
                                         Crop)
        for item in items:
            self.assertContains(response, item.name)

    def test_plagues(self):
        response, items = self.listQuery('plagues', PlaguesListView,
                                         Plague)
        for item in items:
            self.assertContains(response, item.name)
