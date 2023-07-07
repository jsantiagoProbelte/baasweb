from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import Thesis, Replica
from trialapp.data_models import DataModel, ThesisData, ReplicaData,\
    Assessment, SampleData, Sample
from baaswebapp.graphs import GraphTrial
from trialapp.data_views import DataHelper, SetDataAssessment, TrialDataApi,\
    DataGraphFactory
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.tests.tests_trial_analytics import DataGenerator


class DataViewsTest(TestCase):

    _fieldTrial = None
    _theses = []
    _units = []
    _assessments = None
    _apiFactory = None
    _replicas = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_setData(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=False)
        trial = datagenerator._fieldTrials[0]
        emptyAssInfo = {
            'name': 'empty',
            'assessment_date': '2022-05-14',
            'rate_type_id': 1,
            'part_rated': 'LEAF, P',
            'crop_stage_majority': '89, 89, 89',
            'field_trial_id': trial.id}
        assmt = Assessment.objects.create(**emptyAssInfo)
        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 0)
        self.assertEqual(
            dataShow['assessment'].assessment_date.isoformat(),
            assmt.assessment_date)

        theses = Thesis.getObjects(trial, as_dict=True)
        thesis = theses[1]
        thesis2 = theses[2]

        # Let's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    GraphTrial.L_THESIS, assmt, thesis),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post('set_data_point', data=addData)
        self._apiFactory.setUser(addDataPoint)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].assessment.id, assmt.id)
        self.assertEqual(tPoints[0].reference.id, thesis.id)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    GraphTrial.L_THESIS, assmt,
                    thesis), 'data-point': 66}
        addDataPoint = self._apiFactory.post('set_data_point', data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': DataModel.generateDataPointId(
            GraphTrial.L_THESIS, assmt,
            thesis2), 'data-point': 99}
        addDataPoint = self._apiFactory.post('set_data_point', data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPoints = ThesisData.dataPointsAssess([assmt])
        factory = DataGraphFactory(GraphTrial.L_THESIS, [assmt],
                                   dataPoints, references=theses)
        graphToDisplay = factory._graph.bar()
        self.assertTrue(graphToDisplay is not None)
        graphToDisplay = factory._graph.scatter()
        self.assertTrue(graphToDisplay is not None)

        # Let's query via the DataHelper
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 2)
        self.assertEqual(dataShow['level'], GraphTrial.L_THESIS)

    def test_setReplicaData(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=False)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]
        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 0)
        self.assertEqual(
            dataShow['assessment'].assessment_date.isoformat(),
            assmt.assessment_date)

        # Validate when no data yet
        replicas = Replica.getFieldTrialObjects(trial)
        self.assertGreater(len(replicas), 0)

        # for replica in replicas:
        #     idInput = DataModel.generateDataPointId(
        #         GraphTrial.L_REPLICA, self._assessment, replica)
        #     self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', assmt, replicas[0]),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post('set_data_point', data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].assessment.id, assmt.id)
        self.assertEqual(tPoints[0].reference.id, replicas[0].id)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', assmt, replicas[0]),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': DataModel.generateDataPointId(
            'replica', assmt, replicas[1]), 'data-point': 99}
        addDataPoint = self._apiFactory.post('set_data_point', data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 2)
        self.assertEqual(dataShow['level'], GraphTrial.L_REPLICA)
        self.assertEqual(dataShow['stats'], '')

        # View trial_data
        request = self._apiFactory.get('trial_data')
        self._apiFactory.setUser(request)
        apiView = TrialDataApi()
        response = apiView.get(request, pk=trial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, trial.name)

    def test_datalevelsReplica(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=True)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]
        dataHelper = DataHelper(assmt.id)
        replicas = Replica.getFieldTrialObjects(trial)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], len(replicas))
        self.assertEqual(dataShow['level'], GraphTrial.L_REPLICA)
        self.assertTrue(dataShow['stats'] is not None)

    def test_datalevelsThesis(self):
        datagenerator = DataGenerator(thesisGen=True, replicaGen=True)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]
        dataHelper = DataHelper(assmt.id)
        replicas = Replica.getFieldTrialObjects(trial)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], len(replicas))
        self.assertEqual(dataShow['level'], GraphTrial.L_REPLICA)
        self.assertTrue(dataShow['stats'] is not None)

    def incompleteDataset(self, level, references, assmt, classData):
        num_references = len(references)
        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 0)
        self.assertEqual(dataShow['level'], level)
        self.assertEqual(len(dataShow['dataRows']), num_references)
        self.assertEqual(dataShow['graphData'], GraphTrial.NO_DATA_AVAILABLE)
        self.assertNotEqual(dataShow['dataRows'][0]['item_id'], None)
        self.assertTrue(level in dataShow['dataRows'][0]['item_id'])
        if 'sampleCols' in dataShow['dataRows'][0]:
            self.assertTrue(dataShow['dataRows'][0]['sampleCols'] is None)

        # Create an object
        classData.objects.create(value=66,
                                 assessment=assmt,
                                 reference=references[0])
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 1)
        self.assertEqual(dataShow['level'], level)
        self.assertEqual(len(dataShow['dataRows']), num_references)
        self.assertNotEqual(dataShow['graphData'],
                            GraphTrial.NO_DATA_AVAILABLE)
        self.assertNotEqual(dataShow['dataRows'][0]['item_id'], None)
        self.assertTrue(level in dataShow['dataRows'][0]['item_id'])
        self.assertEqual(dataShow['dataRows'][0]['value'], 66)
        if 'sampleCols' in dataShow['dataRows'][0]:
            self.assertTrue(dataShow['dataRows'][0]['sampleCols'] is None)

    def test_incompleteDatasetThesis(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=False)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]

        # Let's pretend no repicas are defined
        trial.replicas_per_thesis = 0
        trial.save()

        self.incompleteDataset(GraphTrial.L_THESIS,
                               Thesis.getObjects(trial),
                               assmt, ThesisData)

    def test_incompleteDatasetReplica(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=False)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]

        self.incompleteDataset(GraphTrial.L_REPLICA,
                               Replica.getFieldTrialObjects(trial),
                               assmt, ReplicaData)

    def test_assessmentSampleIntoSampleDataSet(self):
        datagenerator = DataGenerator(thesisGen=False, replicaGen=False,
                                      sampleGen=True)
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]

        replicas = Replica.getFieldTrialObjects(trial)
        num_replicas = len(replicas)
        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 0)
        self.assertTrue('sample' in dataShow['level'])
        self.assertEqual(len(dataShow['dataRows']), num_replicas)
        self.assertEqual(dataShow['graphData'], GraphTrial.NO_DATA_AVAILABLE)
        self.assertNotEqual(dataShow['dataRows'][0]['item_id'], None)
        self.assertTrue('replica' in dataShow['dataRows'][0]['item_id'])
        self.assertEqual(len(dataShow['dataRows'][0]['sampleCols']),
                         trial.samples_per_replica)
        self.assertTrue('sample' in
                        dataShow['dataRows'][0]['sampleCols'][0]['item_id'])
        self.assertTrue(dataShow['stats'] is None)

        # Create a sample data
        fakeSmpId = 1
        value = 33
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', assmt, replicas[0], fakeSmpId),
                   'data-point': value}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        samples = Sample.objects.all()
        self.assertEqual(len(samples), 1)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, value)
        self.assertEqual(tPoints[0].assessment.id,
                         assmt.id)
        self.assertEqual(tPoints[0].reference.number,
                         fakeSmpId)

        # See that now we do not see the replicaId
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 1)
        self.assertTrue('sample' in dataShow['level'])
        self.assertEqual(len(dataShow['dataRows']), num_replicas)
        self.assertNotEqual(dataShow['graphData'],
                            GraphTrial.NO_DATA_AVAILABLE)
        self.assertEqual(dataShow['dataRows'][0]['item_id'], None)
        self.assertEqual(len(dataShow['dataRows'][0]['sampleCols']),
                         trial.samples_per_replica)
        self.assertEqual(value,
                         dataShow['dataRows'][0]['sampleCols'][0]['value'])
        self.assertTrue(dataShow['stats'] is not None)

        # Now lets simulate that we actualy input a thesis value.
        # lets remove the existing data sample
        tPoints[0].delete()
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 0)
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', assmt, replicas[0]),
                   'data-point': value}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 1)
        self.assertEqual(dataShow['level'], 'replica')
        self.assertEqual(len(dataShow['dataRows']), num_replicas)
        self.assertNotEqual(dataShow['graphData'],
                            GraphTrial.NO_DATA_AVAILABLE)
        self.assertTrue('replica' in dataShow['dataRows'][0]['item_id'])
        self.assertTrue(dataShow['dataRows'][0]['sampleCols'] is None)

    def test_setSampleData(self):
        datagenerator = DataGenerator()
        trial = datagenerator._fieldTrials[0]
        assName = '15 DA-E'
        assmt = datagenerator._assessments[assName]
        replicas = Replica.getFieldTrialObjects(trial)
        fakeSmpId = 1

        # add bad values
        addBadData = {'data_point_id': DataModel.generateDataPointId(
                    'badboy', assmt, replicas[0], fakeSmpId),
                   'data-point': 33}
        addBadDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addBadData)
        apiView = SetDataAssessment()
        response = apiView.post(addBadDataPoint)
        self.assertEqual(response.status_code, 500)

        fakeSmpId = 1
        value = 33
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', assmt, replicas[0], fakeSmpId),
                   'data-point': value}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        samples = Sample.objects.all()
        self.assertEqual(len(samples), 1)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, value)
        self.assertEqual(tPoints[0].assessment.id,
                         assmt.id)
        self.assertEqual(tPoints[0].reference.number,
                         fakeSmpId)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', assmt, replicas[0], fakeSmpId),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': DataModel.generateDataPointId(
            'sample', assmt, replicas[0], fakeSmpId+1),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataHelper = DataHelper(assmt.id)
        dataShow = dataHelper.showDataAssessment()
        self.assertEqual(dataShow['points'], 2)
        self.assertEqual(dataShow['points'], Sample.objects.count())
        self.assertEqual(dataShow['points'], SampleData.objects.count())
        self.assertTrue(dataShow['stats'] is not None)
