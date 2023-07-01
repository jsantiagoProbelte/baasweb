from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import Thesis, Replica
from trialapp.data_models import DataModel, ThesisData, ReplicaData,\
    Assessment
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
        response = apiView.get(request,
                               pk=trial.id)
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
        self.assertEqual(dataShow['graphData'],
                         GraphTrial.NO_DATA_AVAILABLE)

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

    # def test_setSampleData(self):
    #     datagenerator = DataGenerator()
    #     assName = '15 DA-E'
    #     assmt = datagenerator[assName]
    #     dataHelper = DataHelper(assmt.id)
    #     dataPointList, totalPoints = dataHelper.showDataAssessment()
    #     token = DataHelper.TOKEN_LEVEL[GraphTrial.L_SAMPLE]
    #     self.assertEqual(token, 'dataPointsS')
    #     self.assertTrue(
    #         'Number of samples per replica' in
    #         dataPointList[token][0]['errors'])
    #     # we expect a redirect to define a samples per replica,
    #     # since the associated field trial has not defined

    #     # let's set it manually and try again
    #     samplesNum = 25
    #     self._fieldTrial.samples_per_replica = samplesNum
    #     self._fieldTrial.save()
    #     dataHelper._fieldTrial = self._fieldTrial

    #     dataPointList, totalPoints = dataHelper.showDataPerLevel(
    #         GraphTrial.L_SAMPLE, onlyThisData=True)
    #     token = DataHelper.TOKEN_LEVEL[GraphTrial.L_SAMPLE]
    #     self.assertEqual(token, 'dataPointsS')
    #     self.assertFalse(
    #         'Number of samples per replica' in
    #         dataPointList[token][0]['errors'])

    #     # Now, the user should have select a replica and then
    #     # she should get a page to input data per sample, even
    #     # if samples are not created yet. Le's check that
    #     replicas = Replica.getFieldTrialObjects(
    #         self._fieldTrial)
    #     selectedReplica = replicas[0]
    #     samples = Sample.getObjects(selectedReplica)
    #     self.assertEqual(len(samples), 0)
    #     # Realize that we do not need to create he samples anymore.
    #     # We fake them during the view representation,
    #     # and we only create them after data input
    #     #
    #     # we have as many rows as samples
    #     self.assertEqual(len(dataPointList[token][0]['rows']), samplesNum)
    #     fakeSmpId = 16
    #     dataPoints = dataPointList[token][0]['rows'][fakeSmpId-1]
    #       ['dataPoints']
    #     # Extract itemIds
    #     itemIds = []
    #     for dataPoint in dataPoints:
    #         itemIds.append(dataPoint['item_id'])
    #         self.assertEqual(dataPoint['value'], '')
    #     # Per row, we have as many columns as replicas
    #     self.assertEqual(len(itemIds), len(replicas))
    #     # in the same row, we get all the samples for the sample number
    #     for replica in replicas:
    #         idInput = DataModel.generateDataPointId(
    #             GraphTrial.L_SAMPLE, self._assessment, replica, fakeSmpId)
    #         self.assertTrue(idInput in itemIds)

    #     # Le's add data
    #     self.assertEqual(ThesisData.objects.count(), 0)
    #     addData = {'data_point_id': DataModel.generateDataPointId(
    #                 'sample', self._assessment, selectedReplica, fakeSmpId),
    #                'data-point': 33}
    #     addDataPoint = self._apiFactory.post(
    #         'set_data_point',
    #         data=addData)
    #     apiView = SetDataAssessment()
    #     response = apiView.post(addDataPoint)
    #     self.assertEqual(response.status_code, 200)
    #     tPoints = SampleData.objects.all()
    #     self.assertEqual(len(tPoints), 1)
    #     self.assertEqual(tPoints[0].value, 33)
    #     self.assertEqual(tPoints[0].assessment.id,
    #                      self._assessment.id)
    #     self.assertEqual(tPoints[0].reference.number,
    #                      fakeSmpId)

    #     # add bad values
    #     self.assertEqual(ThesisData.objects.count(), 0)
    #     addBadData = {'data_point_id': DataModel.generateDataPointId(
    #                 'badboy', self._assessment, selectedReplica, fakeSmpId),
    #                'data-point': 33}
    #     addBadDataPoint = self._apiFactory.post(
    #         'set_data_point',
    #         data=addBadData)
    #     response = apiView.post(addBadDataPoint)
    #     self.assertEqual(response.status_code, 500)

    #     # modify
    #     addData = {'data_point_id': DataModel.generateDataPointId(
    #                 'sample', self._assessment, selectedReplica, fakeSmpId),
    #                'data-point': 66}
    #     addDataPoint = self._apiFactory.post(
    #         'set_data_point',
    #         data=addData)
    #     response = apiView.post(addDataPoint)
    #     tPoints = SampleData.objects.all()
    #     self.assertEqual(len(tPoints), 1)
    #     self.assertEqual(tPoints[0].value, 66)

    #     # add new point
    #     addData = {'data_point_id': DataModel.generateDataPointId(
    #         'sample', self._assessment, selectedReplica, fakeSmpId+1),
    #         'data-point': 99}
    #     addDataPoint = self._apiFactory.post(
    #         'set_data_point',
    #         data=addData)
    #     response = apiView.post(addDataPoint)
    #     tPoints = SampleData.objects.all()
    #     self.assertEqual(len(tPoints), 2)
    #     self.assertEqual(tPoints[1].value, 99)

    #     dataPointList, totalPoints = dataHelper.showDataPerLevel(
    #         GraphTrial.L_SAMPLE, onlyThisData=True)
    #     self.assertEqual(totalPoints, 2)
    #     self.assertEqual(totalPoints, Sample.objects.count())
    #     self.assertEqual(totalPoints, SampleData.objects.count())
