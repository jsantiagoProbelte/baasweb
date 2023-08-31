from django.test import TestCase
from baaswebapp.models import ModelHelpers
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Crop, Plague, \
                            Thesis, Sample, Replica, TrialType
from trialapp.data_models import ThesisData, SampleData, Assessment
import datetime
from trialapp.tests.tests_helpers import TrialTestData
from django.utils.translation import gettext_lazy as _


class TrialAppModelTest(TestCase):
    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_avoidduplicates(self):
        crops = Crop.objects.count()
        self.assertTrue(crops > 0)
        types = TrialType.objects.count()
        self.assertTrue(types > 0)
        TrialDbInitialLoader.loadInitialTrialValues()
        crops2 = Crop.objects.count()
        self.assertEqual(crops, crops2)
        types2 = TrialType.objects.count()
        self.assertEqual(types, types2)

    def test_ModelHelpers(self):
        unknownCrop = Crop.getUnknown()
        self.assertEqual(unknownCrop.name, ModelHelpers.UNKNOWN)
        self.assertTrue(unknownCrop.isUnknown())

        itemsFromObjectsAll = Crop.objects.all()
        len_itemsFromObjectsAll = len(itemsFromObjectsAll)
        self.assertGreater(len_itemsFromObjectsAll, 0)

        initValues = TrialDbInitialLoader.initialTrialModelComplexValues()
        cropValues = list(initValues[Crop].keys())
        len_cropValues = len(cropValues)
        self.assertEqual(len_itemsFromObjectsAll,
                         len_cropValues)

        for item in itemsFromObjectsAll:
            self.assertTrue(item.name in cropValues)

        itemsGetObjects = Crop.getObjects()
        len_itemsGetObjects = len(itemsGetObjects)
        self.assertGreater(len_itemsGetObjects, 0)
        for item in itemsGetObjects:
            self.assertTrue(item.name in cropValues)

        self.assertEqual(len_itemsFromObjectsAll, len_itemsGetObjects)
        self.assertEqual(len_itemsGetObjects, len_cropValues)

        theList = Crop.getSelectList()
        self.assertEqual(len(theList), len_cropValues)
        self.assertTrue(theList[0][1] in cropValues)

        theList = Crop.getSelectList(addNull=True)
        self.assertEqual(len(theList), len_cropValues+1)
        self.assertEqual(theList[0][1], ModelHelpers.NULL_STRING)
        self.assertEqual(theList[0][0], None)

        theArray = Crop.getSelectList(asDict=True)
        self.assertEqual(len(theArray), len_cropValues)
        self.assertTrue(theArray[0]['name'] in cropValues)

    def test_fixtures(self):
        trial666 = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        self.assertEqual(trial666.name,
                         TrialTestData.TRIALS[0]['name'])

        thesis666 = Thesis.createThesis(
            **TrialTestData.THESIS[0])
        self.assertEqual(thesis666.name,
                         TrialTestData.THESIS[0]['name'])

    def test_names(self):
        for model in TrialDbInitialLoader.initialTrialModelValues():
            instance = model.objects.get(pk=1)
            self.assertEqual(instance.name,
                             instance.__str__())

    def test_dataPoints(self):
        fieldTrial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        thesis = Thesis.createThesis(**TrialTestData.THESIS[0])
        assessment = Assessment.objects.create(
            name='eval1',
            assessment_date='2022-12-15',
            field_trial=fieldTrial,
            rate_type_id=1,
            crop_stage_majority=65)
        dataPoints = ThesisData.getDataPoints(assessment)
        self.assertEqual(len(dataPoints), 0)
        ThesisData.setDataPoint(thesis, assessment, 33)
        dataPoints = ThesisData.getDataPoints(assessment)
        self.assertEqual(len(dataPoints), 1)
        ThesisData.setDataPoint(thesis, assessment, 66)
        self.assertEqual(len(dataPoints), 1)

        toCreate = 4
        Replica.createReplicas(thesis, toCreate)
        replicas = Replica.getObjects(thesis)
        self.assertEqual(len(replicas), toCreate)
        selectedReplica = replicas[0]
        selectedReplica.name = None
        selectedReplica.save()
        self.assertEqual(
            selectedReplica.getName(),
            '[{}-{}] {}-({},{})'.format(
                selectedReplica.thesis.number,
                selectedReplica.thesis.name,
                selectedReplica.number,
                selectedReplica.pos_x,
                selectedReplica.pos_y))
        selectedReplica.name = '666'
        self.assertEqual(
            selectedReplica.getName(),
            selectedReplica.name)

        toCreate = 4
        Sample.createSamples(selectedReplica, toCreate)
        samples = Sample.getObjects(selectedReplica)
        self.assertEqual(len(samples), toCreate)
        selectedSample = samples[0]

        self.assertEqual(
            selectedSample.getName(),
            '[{}-{}] {}-({})'.format(
                selectedSample.replica.thesis.number,
                selectedSample.replica.thesis.name,
                selectedSample.replica.number,
                selectedSample.number))

        SampleData.objects.create(
            assessment=assessment,
            reference=selectedSample,
            value=66)

        sampleData = SampleData.getDataPointsPerSampleNumber(
            assessment, selectedReplica.number)
        self.assertEqual(len(sampleData), 1)

    def test_fieldTrial_planDensity(self):
        fieldTrial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        dBp = 2.2
        dBr = 0.5
        self.assertEqual(fieldTrial.plantDensity(), None)
        fieldTrial.distance_between_plants = dBp
        self.assertEqual(fieldTrial.plantDensity(), None)
        fieldTrial.distance_between_rows = dBr
        self.assertEqual(fieldTrial.plantDensity(),
                         round(10000/(dBp*dBr), 2))

    def test_code_fieldTrial(self):
        hoy = datetime.date.today()
        year = hoy.year
        month = hoy.month
        code = FieldTrial.getCode(hoy, True)
        counts = FieldTrial.objects.count()
        self.assertEqual(counts, 0)
        expectedCode = FieldTrial.formatCode(year, month, counts + 1)
        self.assertEqual(code, expectedCode)
        code = FieldTrial.getCode(hoy, False)
        expectedCode = FieldTrial.formatCode(year, month, counts)
        self.assertEqual(code, expectedCode)
        fieldTrial = FieldTrial.createTrial(
            **TrialTestData.TRIALS[0])
        counts = FieldTrial.objects.count()
        self.assertEqual(counts, 1)
        expectedCode = FieldTrial.formatCode(year, month, counts)
        self.assertEqual(fieldTrial.code, expectedCode)
        fieldTrial.code = None
        fieldTrial.save()

    def test_thesis_extras(self):
        fieldTrial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        code = Thesis.computeNumber(fieldTrial, True)
        counts = Thesis.objects.count()
        self.assertEqual(counts, 0)
        self.assertEqual(code, counts + 1)
        code = Thesis.computeNumber(fieldTrial, False)
        self.assertEqual(code, 0)
        thesis = Thesis.createThesis(
            **TrialTestData.THESIS[0])
        counts = Thesis.objects.count()
        self.assertEqual(counts, 1)
        self.assertEqual(thesis.number, counts)

    def test_plague_name(self):
        p1 = Plague.objects.create(name='name1')
        p2 = Plague.objects.create(name='name2', scientific='sctf2')
        self.assertEqual(p1.getName(), p1.name)
        self.assertEqual(p2.getName(), p2.scientific)

    def test_findOrCreate(self):
        crops = Crop.getObjects()
        lastOne = len(crops) - 1
        crop1 = crops[lastOne]
        cropNew = Crop.findOrCreate(name=crop1.name)
        self.assertEqual(crop1.id, cropNew.id)

        cropNew = Crop.findOrCreate(name='Cropy')
        self.assertTrue(crop1.id < cropNew.id)

        cropNew2 = Crop.findOrCreate(name='Cropy2',
                                     scientific='Scientific')
        self.assertTrue(cropNew.id < cropNew2.id)
        self.assertEqual(cropNew2.scientific, 'Scientific')

    def test_trialfunctions(self):
        FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        trial = FieldTrial.objects.get(id=1)
        sameYear = trial.initiation_date.year
        sameYearStr = f'{sameYear}'
        sameMonthStr = trial.initiation_date.strftime("%B")
        sameMonth = trial.initiation_date.month
        self.assertTrue(trial.completion_date is None)
        self.assertTrue(trial.getPeriod()[:-5], '- ...')
        trial.completion_date = datetime.date(sameYear, sameMonth, 14)
        trial.save()
        period = trial.getPeriod()
        self.assertTrue('-' not in trial.getPeriod())
        self.assertEqual(period.count(sameYearStr), 1)
        self.assertEqual(period.count(sameMonthStr), 1)

        trial.completion_date = datetime.date(sameYear, sameMonth + 1, 14)
        trial.save()
        period = trial.getPeriod()
        self.assertEqual(period.count(sameYearStr), 1)
        self.assertEqual(period.count(sameMonthStr), 1)
        self.assertTrue(trial.completion_date.strftime("%B") in period)
        self.assertTrue('-' in period)

        trial.completion_date = datetime.date(sameYear+1, sameMonth + 1, 14)
        trial.save()
        period = trial.getPeriod()
        self.assertEqual(period.count(sameYearStr), 1)
        self.assertEqual(period.count(sameMonthStr), 1)
        self.assertTrue(trial.completion_date.strftime("%B") in period)
        self.assertTrue(f"{sameYear+1}" in period)
        self.assertTrue('-' in period)

        trial.initiation_date = None
        trial.completion_date = None
        trial.save()
        self.assertEqual(trial.getPeriod(), _('Undefined period'))

        self.assertNotEqual(trial.getLocation(), _('Undefined Location'))
        trial.location = None
        trial.save()
        self.assertEqual(trial.getLocation(), _('Undefined Location'))

        trial.plague = None
        trial.save()
        self.assertTrue(trial.getDescription(), trial.crop)
        trial.plague_id = 3
        trial.save()
        desc = trial.getDescription()
        self.assertTrue(trial.crop.name in desc)
        self.assertTrue(trial.plague.name in desc)
        trial.plague = Plague.objects.get(name=ModelHelpers.NOT_APPLICABLE)
        trial.save()
        desc = trial.getDescription()
        self.assertTrue(trial.crop.name in desc)
        self.assertTrue(trial.plague.name not in desc)
