from django.test import TestCase
from baaswebapp.models import ModelHelpers
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Crop, Plague,\
                            Thesis, Evaluation,\
                            TrialAssessmentSet,\
                            AssessmentType, AssessmentUnit,\
                            Sample, Replica, TrialType
from trialapp.data_models import ThesisData, SampleData
import datetime


# Create your tests here.
class TrialAppModelTest(TestCase):

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
            'blocks': 3,
            'type': 1,
            'status': 1}
    ]

    THESIS = [{
        'name': 'thesis 666',
        'description': 'Thesis 666 for product 1',
        'field_trial_id': 1,
        'number_applications': 5,
        'interval': 14,
        'first_application': '2021-01-01',
        # 'mode': 1 Use mode and not mode_id in post calls
        }, {
        'name': 'thesis 777',
        'description': 'Thesis 777 for product 2',
        'field_trial_id': 1,
        'number_applications': 5,
        'interval': 7,
        'first_application': '2021-01-01',
        'mode_id': 2
        }
    ]

    PRODUCT_THESIS = [{
        'thesis_id': 1,
        'product_id': 1,
        'rate': 1.5,
        'rate_unit_id': 1},
        {
        'thesis_id': 1,
        'product_id': 2,
        'rate': 5,
        'rate_unit_id': 1},
        {
        'thesis_id': 2,
        'product_id': 1,
        'rate': 3,
        'rate_unit_id': 1}
    ]

    EVALUATION = [{
        'field_trial_id': 1,
        'name': 'Primera aplication',
        'evaluation_date': '2022-07-01',
        'crop_stage_majority': 66
    }]

    APPLICATION = [{
        'field_trial_id': 1,
        'comment': 'Primera aplication',
        'app_date': '2022-07-01',
        'bbch': 66
        },
        {
        'field_trial_id': 1,
        'comment': 'segunda aplication',
        'app_date': '2022-07-17',
        'bbch': 67},
        {
        'field_trial_id': 1,
        'comment': 'segunda aplication',
        'app_date': '2022-07-10',
        'bbch': 67
    }]

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
        fieldTrial666 = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        self.assertEqual(fieldTrial666.name,
                         TrialAppModelTest.FIELDTRIALS[0]['name'])

        thesis666 = Thesis.create_Thesis(
            **TrialAppModelTest.THESIS[0])
        self.assertEqual(thesis666.name,
                         TrialAppModelTest.THESIS[0]['name'])

    def test_names(self):
        for model in TrialDbInitialLoader.initialTrialModelValues():
            instance = model.objects.get(pk=1)
            self.assertEqual(instance.name,
                             instance.__str__())

    def test_dataPoints(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        thesis = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        assSet = TrialAssessmentSet.objects.create(
            field_trial=fieldTrial,
            type=AssessmentType.objects.get(pk=1),
            unit=AssessmentUnit.objects.get(pk=1))
        evaluation = Evaluation.objects.create(
            name='eval1',
            evaluation_date='2022-12-15',
            field_trial=fieldTrial,
            crop_stage_majority=65)
        dataPoints = ThesisData.getDataPoints(evaluation)
        self.assertEqual(len(dataPoints), 0)
        ThesisData.setDataPoint(thesis, evaluation, assSet, 33)
        dataPoints = ThesisData.getDataPoints(evaluation)
        self.assertEqual(len(dataPoints), 1)
        ThesisData.setDataPoint(thesis, evaluation, assSet, 66)
        self.assertEqual(len(dataPoints), 1)
        assset = TrialAssessmentSet.getObjects(fieldTrial)
        self.assertEqual(assset[0].unit, assSet.unit)

        toCreate = 4
        Replica.createReplicas(thesis, toCreate)
        replicas = Replica.getObjects(thesis)
        self.assertEqual(len(replicas), toCreate)
        selectedReplica = replicas[0]
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

        self.assertEqual(
            selectedSample.getShortName(),
            '{}-[{}]-{}'.format(
                selectedSample.replica.thesis.name,
                selectedSample.replica.number,
                selectedSample.number))

        SampleData.objects.create(
            evaluation=evaluation,
            reference=selectedSample,
            unit=assset[0],
            value=66)

        sampleData = SampleData.getDataPointsPerSampleNumber(
            evaluation, assset[0], selectedReplica.number)
        self.assertEqual(len(sampleData), 1)

    def test_fieldTrial_planDensity(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
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
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        counts = FieldTrial.objects.count()
        self.assertEqual(counts, 1)
        expectedCode = FieldTrial.formatCode(year, month, counts)
        self.assertEqual(fieldTrial.code, expectedCode)
        fieldTrial.code = None
        fieldTrial.save()

    def test_thesis_extras(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        code = Thesis.computeNumber(fieldTrial, True)
        counts = Thesis.objects.count()
        self.assertEqual(counts, 0)
        self.assertEqual(code, counts + 1)
        code = Thesis.computeNumber(fieldTrial, False)
        self.assertEqual(code, 0)
        thesis = Thesis.create_Thesis(
            **TrialAppModelTest.THESIS[0])
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
