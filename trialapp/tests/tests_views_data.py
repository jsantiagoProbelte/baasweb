from django.test import TestCase
from baaswebapp.models import RateTypeUnit
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica, Sample
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.data_models import DataModel, ThesisData, ReplicaData,\
    SampleData, Assessment
from baaswebapp.graphs import GraphTrial
from trialapp.data_views import DataHelper, SetDataAssessment
from baaswebapp.tests.test_views import ApiRequestHelperTest


class DataViewsTest(TestCase):

    _fieldTrial = None
    _theses = []
    _units = []
    _assessment = None
    _apiFactory = None
    _replicas = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            self._theses.append(Thesis.create_Thesis(**thesis))

        Replica.createReplicas(
            self._theses[0],
            self._fieldTrial.replicas_per_thesis)
        self._replicas = Replica.getObjects(self._theses[0])

        rateTypes = RateTypeUnit.objects.all()
        self._units = [rateTypes[i] for i in range(1, 3)]

        self._assessment = Assessment.objects.create(
            name='eval1',
            assessment_date='2022-12-15',
            field_trial=self._fieldTrial,
            rate_type=self._units[0],
            crop_stage_majority=65)

    def test_setData(self):
        dataHelper = DataHelper(self._assessment.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_THESIS, onlyThisData=True)
        self.assertEqual(totalPoints, 0)

        token = DataHelper.TOKEN_LEVEL[GraphTrial.L_THESIS]
        self.assertEqual(token, 'dataPointsT')
        self.assertEqual(len(dataPointList[token]), 1)
        self.assertEqual(
            dataPointList[token][0]['rows'][0]['index'].isoformat(),
            self._assessment.assessment_date)

        dataPoints = dataPointList[token][0]['rows'][0]['dataPoints']
        # Extract itemIds
        itemIds = []
        for dataPoint in dataPoints:
            itemIds.append(dataPoint['item_id'])
            self.assertEqual(dataPoint['value'], '')
        theses = Thesis.getObjects(dataHelper._fieldTrial)
        self.assertEqual(len(itemIds), len(theses))
        for thesis in theses:
            idInput = DataModel.generateDataPointId(
                GraphTrial.L_THESIS, self._assessment, thesis)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    GraphTrial.L_THESIS, self._assessment,
                    self._theses[0]),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].assessment.id,
                         self._assessment.id)
        self.assertEqual(tPoints[0].reference.id,
                         self._theses[0].id)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    GraphTrial.L_THESIS, self._assessment,
                    self._theses[0],
                    ),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': DataModel.generateDataPointId(
            GraphTrial.L_THESIS, self._assessment,
            self._theses[1],
            ),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPoints = ThesisData.getDataPoints(self._assessment)
        graph = GraphTrial(GraphTrial.L_THESIS, self._units[0],
                           'part', dataPoints)
        graphToDisplay = graph.bar()
        self.assertTrue(graphToDisplay is not None)
        graphToDisplay = graph.scatter()
        self.assertTrue(graphToDisplay is not None)

        # Let's query via the DataHelper
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_THESIS, onlyThisData=True)
        self.assertEqual(totalPoints, 2)

    def test_graph_logic(self):
        thesis = self._theses[0]
        unit = self._units[0]
        dPT = ThesisData.objects.create(
            assessment=self._assessment,
            reference=thesis,
            value=33)

        replica = self._replicas[0]
        dPR = ReplicaData.objects.create(
            assessment=self._assessment,
            reference=replica,
            value=66)

        Sample.createSamples(replica, 5)
        samples = Sample.getObjects(replica)
        sample = samples[0]

        dPS = SampleData.objects.create(
            assessment=self._assessment,
            reference=sample,
            value=66)

        graphT = GraphTrial(GraphTrial.L_THESIS, unit, 'part', [dPT])
        graphR = GraphTrial(GraphTrial.L_REPLICA, unit, 'part', [dPR])
        graphS = GraphTrial(GraphTrial.L_SAMPLE, unit, 'part', [dPS])
        traceId = unit.id
        code = thesis.field_trial.code
        self.assertEqual(graphT.traceId(dPT),
                         "{}".format(thesis.number))
        self.assertEqual(graphR.traceId(dPR),
                         "{}".format(thesis.number))
        self.assertEqual(graphS.traceId(dPS),
                         "{}".format(replica.number))

        self.assertEqual(graphT.getTraceName(dPT, code), thesis.name)
        self.assertEqual(graphR.getTraceName(dPR, code), thesis.name)
        self.assertEqual(graphS.getTraceName(dPS, code), thesis.name)

        graphT._combineTrialAssessments = True
        self.assertEqual(graphT.traceId(dPT),
                         "{}-{}".format(thesis.number, traceId))
        self.assertEqual(graphT.getTraceName(dPT, code),
                         "{}-{}".format(thesis.name, code))

        color = GraphTrial.COLOR_LIST[thesis.number]
        self.assertEqual(graphT.getTraceColor(dPT), color)
        self.assertEqual(graphR.getTraceColor(dPR), color)
        self.assertEqual(graphS.getTraceColor(dPS), color)

        symbolT = GraphTrial.SYMBOL_LIST[2]
        symbolR = GraphTrial.SYMBOL_LIST[replica.number]
        self.assertEqual(graphT.getTraceSymbol(dPT), symbolT)
        self.assertEqual(graphR.getTraceSymbol(dPR), symbolR)
        self.assertEqual(graphS.getTraceSymbol(dPS), symbolR)

        graphSOne = GraphTrial(GraphTrial.L_SAMPLE, self._units[0], 'part',
                               [dPS], combineTrialAssessments=True)
        self.assertEqual(graphSOne.traceId(dPS),
                         "{}-{}".format(replica.number, self._units[0].id))

    def test_setReplicaData(self):
        dataHelper = DataHelper(self._assessment.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_REPLICA, onlyThisData=True)
        self.assertEqual(totalPoints, 0)
        # self.assertContains(response, 'assessment, add data per thesis')
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        self.assertGreater(len(replicas), 0)

        token = DataHelper.TOKEN_LEVEL[GraphTrial.L_REPLICA]
        self.assertEqual(token, 'dataPointsR')
        self.assertEqual(len(dataPointList[token]), 1)
        self.assertEqual(
            dataPointList[token][0]['rows'][0]['index'].isoformat(),
            self._assessment.assessment_date)

        dataPoints = dataPointList[token][0]['rows'][0]['dataPoints']
        # Extract itemIds
        itemIds = []
        for dataPoint in dataPoints:
            itemIds.append(dataPoint['item_id'])
            self.assertEqual(dataPoint['value'], '')
        self.assertEqual(len(itemIds), len(replicas))
        for thesis in replicas:
            idInput = DataModel.generateDataPointId(
                GraphTrial.L_REPLICA, self._assessment, thesis)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', self._assessment, replicas[0]),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].assessment.id,
                         self._assessment.id)
        self.assertEqual(tPoints[0].reference.id,
                         replicas[0].id)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', self._assessment, replicas[0]),
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
            'replica', self._assessment, replicas[1]),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataHelper = DataHelper(self._assessment.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_REPLICA, onlyThisData=True)
        self.assertEqual(totalPoints, 2)

    def test_setSampleData(self):
        dataHelper = DataHelper(self._assessment.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_SAMPLE, onlyThisData=True)
        token = DataHelper.TOKEN_LEVEL[GraphTrial.L_SAMPLE]
        self.assertEqual(token, 'dataPointsS')
        self.assertTrue(
            'Number of samples per replica' in
            dataPointList[token][0]['errors'])
        # we expect a redirect to define a samples per replica,
        # since the associated field trial has not defined

        # let's set it manually and try again
        samplesNum = 25
        self._fieldTrial.samples_per_replica = samplesNum
        self._fieldTrial.save()
        dataHelper._fieldTrial = self._fieldTrial

        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_SAMPLE, onlyThisData=True)
        token = DataHelper.TOKEN_LEVEL[GraphTrial.L_SAMPLE]
        self.assertEqual(token, 'dataPointsS')
        self.assertFalse(
            'Number of samples per replica' in
            dataPointList[token][0]['errors'])

        # Now, the user should have select a replica and then
        # she should get a page to input data per sample, even
        # if samples are not created yet. Le's check that
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        selectedReplica = replicas[0]
        samples = Sample.getObjects(selectedReplica)
        self.assertEqual(len(samples), 0)
        # Realize that we do not need to create he samples anymore.
        # We fake them during the view representation,
        # and we only create them after data input
        #
        # we have as many rows as samples
        self.assertEqual(len(dataPointList[token][0]['rows']), samplesNum)
        fakeSmpId = 16
        dataPoints = dataPointList[token][0]['rows'][fakeSmpId-1]['dataPoints']
        # Extract itemIds
        itemIds = []
        for dataPoint in dataPoints:
            itemIds.append(dataPoint['item_id'])
            self.assertEqual(dataPoint['value'], '')
        # Per row, we have as many columns as replicas
        self.assertEqual(len(itemIds), len(replicas))
        # in the same row, we get all the samples for the sample number
        for replica in replicas:
            idInput = DataModel.generateDataPointId(
                GraphTrial.L_SAMPLE, self._assessment, replica, fakeSmpId)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', self._assessment, selectedReplica, fakeSmpId),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataAssessment()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].assessment.id,
                         self._assessment.id)
        self.assertEqual(tPoints[0].reference.number,
                         fakeSmpId)

        # add bad values
        self.assertEqual(ThesisData.objects.count(), 0)
        addBadData = {'data_point_id': DataModel.generateDataPointId(
                    'badboy', self._assessment, selectedReplica, fakeSmpId),
                   'data-point': 33}
        addBadDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addBadData)
        response = apiView.post(addBadDataPoint)
        self.assertEqual(response.status_code, 500)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', self._assessment, selectedReplica, fakeSmpId),
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
            'sample', self._assessment, selectedReplica, fakeSmpId+1),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            GraphTrial.L_SAMPLE, onlyThisData=True)
        self.assertEqual(totalPoints, 2)
        self.assertEqual(totalPoints, Sample.objects.count())
        self.assertEqual(totalPoints, SampleData.objects.count())
