from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Crop
from catalogue.models import Product
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.filter_helpers import TrialFilterHelper


class TrialFilterTest(TestCase):
    FIRST_YEAR = 2000

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        # Create as many as trials as assessments to try
        # different conditions
        numP = Product.objects.count()
        numC = Crop.objects.count()

        for i in range(1, numP+1):
            for j in range(1, numC+1):
                trialData = TrialAppModelTest.FIELDTRIALS[0].copy()
                trialData['name'] = f"trial{i}-{j}"
                trialData['product'] = i
                trialData['crop'] = j
                year = TrialFilterTest.FIRST_YEAR + j
                trialData['initiation_date'] = f'{year}-07-01'
                FieldTrial.create_fieldTrial(**trialData)

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

    def test_cropfilter(self):
        # we are going to filter for 1 crop
        # we have create 1 trial per crop and product
        expectedProducts = Product.objects.count()
        for posibleFilter in [{'crop': '1'}]:
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
            self.assertEqual(fHelper.generateParamUrl(), '&crop=1')

            productId = 1
            firstYear = TrialFilterTest.FIRST_YEAR + productId
            rangeYears = f'{firstYear}'
            theProduct = Product.objects.get(id=productId)
            self.assertEqual(fHelper.getMinMaxYears(
                {'product': theProduct}), rangeYears)

            # add unknown product
            otherP = Product.objects.create(name='whatever')
            self.assertEqual(fHelper.getMinMaxYears(
                {'product': otherP}), '-')

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
