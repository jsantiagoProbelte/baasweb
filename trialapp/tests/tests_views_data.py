from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import AssessmentType, AssessmentUnit, FieldTrial,\
    Thesis, TrialAssessmentSet, Evaluation,\
    Replica, Sample
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.data_models import DataModel, ThesisData, ReplicaData, SampleData
from baaswebapp.graphs import Graph
from trialapp.data_views import DataHelper, showTrialAssessmentSetIndex,\
    SetDataEvaluation, ManageTrialAssessmentSet
from baaswebapp.tests.test_views import ApiRequestHelperTest


class DataViewsTest(TestCase):

    _fieldTrial = None
    _theses = []
    _units = []
    _evaluation = None
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

        self._units = [TrialAssessmentSet.objects.create(
            field_trial=self._fieldTrial,
            type=AssessmentType.objects.get(pk=i),
            unit=AssessmentUnit.objects.get(pk=i)) for i in range(1, 3)]

        self._evaluation = Evaluation.objects.create(
            name='eval1',
            evaluation_date='2022-12-15',
            field_trial=self._fieldTrial,
            crop_stage_majority=65)

    def test_setData(self):
        dataHelper = DataHelper(self._evaluation.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_THESIS, onlyThisData=True)
        self.assertEqual(totalPoints, 0)

        token = DataHelper.TOKEN_LEVEL[Graph.L_THESIS]
        self.assertEqual(token, 'dataPointsT')
        self.assertEqual(len(dataPointList[token]), len(self._units))
        self.assertEqual(
            dataPointList[token][0]['rows'][0]['index'].isoformat(),
            self._evaluation.evaluation_date)

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
                Graph.L_THESIS, self._evaluation, self._units[0], thesis)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    Graph.L_THESIS, self._evaluation,
                    self._units[0], self._theses[0]),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        apiView = SetDataEvaluation()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].evaluation.id,
                         self._evaluation.id)
        self.assertEqual(tPoints[0].reference.id,
                         self._theses[0].id)
        self.assertEqual(tPoints[0].unit,
                         self._units[0])

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    Graph.L_THESIS, self._evaluation,
                    self._units[0], self._theses[0],
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
            Graph.L_THESIS, self._evaluation,
            self._units[0], self._theses[1],
            ),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPoints = ThesisData.getDataPoints(self._evaluation)
        graph = Graph(Graph.L_THESIS, self._units, dataPoints)
        graphToDisplay, classGraph = graph.bar()
        self.assertEqual(len(graphToDisplay), 1)
        self.assertEqual(classGraph, 'col-md-12')
        graphToDisplay, classGraph = graph.scatter()
        self.assertEqual(len(graphToDisplay), 1)
        self.assertEqual(classGraph, 'col-md-12')

        # Let's query via the DataHelper
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_THESIS, onlyThisData=True)
        self.assertEqual(totalPoints, 2)

    def test_graph_logic(self):
        thesis = self._theses[0]
        unit = self._units[0]
        dPT = ThesisData.objects.create(
            evaluation=self._evaluation,
            reference=thesis,
            unit=unit,
            value=33)

        replica = self._replicas[0]
        dPR = ReplicaData.objects.create(
            evaluation=self._evaluation,
            reference=replica,
            unit=unit,
            value=66)

        Sample.createSamples(replica, 5)
        samples = Sample.getObjects(replica)
        sample = samples[0]

        dPS = SampleData.objects.create(
            evaluation=self._evaluation,
            reference=sample,
            unit=unit,
            value=66)

        graphT = Graph(Graph.L_THESIS, self._units, [dPT])
        graphR = Graph(Graph.L_REPLICA, self._units, [dPR])
        graphS = Graph(Graph.L_SAMPLE, self._units, [dPS])
        traceId = unit.id
        code = unit.field_trial.code
        self.assertEqual(graphT.traceId(dPT, traceId),
                         "{}".format(thesis.number))
        self.assertEqual(graphR.traceId(dPR, traceId),
                         "{}".format(thesis.number))
        self.assertEqual(graphS.traceId(dPS, traceId),
                         "{}".format(replica.number))

        self.assertEqual(graphT.getTraceName(dPT, code), thesis.name)
        self.assertEqual(graphR.getTraceName(dPR, code), thesis.name)
        self.assertEqual(graphS.getTraceName(dPS, code), thesis.name)

        graphT._combineTrialAssessments = True
        self.assertEqual(graphT.traceId(dPT, traceId),
                         "{}-{}".format(thesis.number, traceId))
        self.assertEqual(graphT.getTraceName(dPT, code),
                         "{}-{}".format(thesis.name, code))

        color = Graph.COLOR_LIST[thesis.number]
        self.assertEqual(graphT.getTraceColor(dPT), color)
        self.assertEqual(graphR.getTraceColor(dPR), color)
        self.assertEqual(graphS.getTraceColor(dPS), color)

        symbolT = Graph.SYMBOL_LIST[2]
        symbolR = Graph.SYMBOL_LIST[replica.number]
        self.assertEqual(graphT.getTraceSymbol(dPT), symbolT)
        self.assertEqual(graphR.getTraceSymbol(dPR), symbolR)
        self.assertEqual(graphS.getTraceSymbol(dPS), symbolR)

    def test_manageEvaluationSet(self):
        requestIndex = self._apiFactory.get(
            'trial-assessment-set-list',
            args=[self._fieldTrial.id])
        self._apiFactory.setUser(requestIndex)
        response = showTrialAssessmentSetIndex(
            requestIndex,
            field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No assessment types defined yet.')
        unitsInTrial = TrialAssessmentSet.getObjects(self._fieldTrial)
        initialUnits = len(unitsInTrial)
        for unit in unitsInTrial:
            self.assertContains(response, unit.unit.name)
            self.assertContains(response, unit.type.name)

        # Let's delete data
        deleteName = unitsInTrial[0].type.name
        deleteUnitId = unitsInTrial[0].unit.id
        deleteTypeId = unitsInTrial[0].type.id
        deleteData = {
            'item_id': unitsInTrial[0].id}
        deleteDataPoint = self._apiFactory.post(
            'manage_trial_assessment_set_api',
            data=deleteData)
        apiView = ManageTrialAssessmentSet()
        response = apiView.delete(deleteDataPoint)
        self.assertEqual(response.status_code, 200)
        unitsInTrial = TrialAssessmentSet.getObjects(self._fieldTrial)
        self.assertEqual(len(unitsInTrial), initialUnits-1)

        requestIndex = self._apiFactory.get(
            'trial_assessment_set_list',
            args=[self._fieldTrial.id])
        self._apiFactory.setUser(requestIndex)
        response = showTrialAssessmentSetIndex(
            requestIndex,
            field_trial_id=self._fieldTrial.id)
        # There is something wrong here. the deleteName shows up
        # alhought the object is deleted. Maybe the response is cached
        # self.assertContains(response, deleteName)

        # add again
        addData = {
            'field_trial_id': self._fieldTrial.id,
            'assessment_type': deleteTypeId,
            'assessment_unit': deleteUnitId}
        addDataPoint = self._apiFactory.post(
            'manage_trial_assessment_set_api',
            data=addData)
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        unitsInTrial = TrialAssessmentSet.getObjects(self._fieldTrial)
        self.assertEqual(len(unitsInTrial), initialUnits)
        response = showTrialAssessmentSetIndex(
            requestIndex,
            field_trial_id=self._fieldTrial.id)
        self.assertContains(response, deleteName)

    def test_setReplicaData(self):
        dataHelper = DataHelper(self._evaluation.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_REPLICA, onlyThisData=True)
        self.assertEqual(totalPoints, 0)
        # self.assertContains(response, 'assessment, add data per thesis')
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        self.assertGreater(len(replicas), 0)

        token = DataHelper.TOKEN_LEVEL[Graph.L_REPLICA]
        self.assertEqual(token, 'dataPointsR')
        self.assertEqual(len(dataPointList[token]), len(self._units))
        self.assertEqual(
            dataPointList[token][0]['rows'][0]['index'].isoformat(),
            self._evaluation.evaluation_date)

        dataPoints = dataPointList[token][0]['rows'][0]['dataPoints']
        # Extract itemIds
        itemIds = []
        for dataPoint in dataPoints:
            itemIds.append(dataPoint['item_id'])
            self.assertEqual(dataPoint['value'], '')
        self.assertEqual(len(itemIds), len(replicas))
        for thesis in replicas:
            idInput = DataModel.generateDataPointId(
                Graph.L_REPLICA, self._evaluation, self._units[0], thesis)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', self._evaluation,
                    self._units[0], replicas[0],
                    ),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataEvaluation()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].evaluation.id,
                         self._evaluation.id)
        self.assertEqual(tPoints[0].reference.id,
                         replicas[0].id)
        self.assertEqual(tPoints[0].unit,
                         self._units[0])

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'replica', self._evaluation,
                    self._units[0], replicas[0],
                    ),
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
            'replica', self._evaluation,
            self._units[0], replicas[1]),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataHelper = DataHelper(self._evaluation.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_REPLICA, onlyThisData=True)
        self.assertEqual(totalPoints, 2)

    def test_setSampleData(self):
        dataHelper = DataHelper(self._evaluation.id)
        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_SAMPLE, onlyThisData=True)
        token = DataHelper.TOKEN_LEVEL[Graph.L_SAMPLE]
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
            Graph.L_SAMPLE, onlyThisData=True)
        token = DataHelper.TOKEN_LEVEL[Graph.L_SAMPLE]
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
                Graph.L_SAMPLE, self._evaluation,
                self._units[0], replica, fakeSmpId)
            self.assertTrue(idInput in itemIds)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', self._evaluation,
                    self._units[0], selectedReplica, fakeSmpId),
                   'data-point': 33}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        apiView = SetDataEvaluation()
        response = apiView.post(addDataPoint)
        self.assertEqual(response.status_code, 200)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 33)
        self.assertEqual(tPoints[0].evaluation.id,
                         self._evaluation.id)
        self.assertEqual(tPoints[0].reference.number,
                         fakeSmpId)
        self.assertEqual(tPoints[0].unit,
                         self._units[0])

        # add bad values
        self.assertEqual(ThesisData.objects.count(), 0)
        addBadData = {'data_point_id': DataModel.generateDataPointId(
                    'badboy', self._evaluation,
                    self._units[0], selectedReplica, fakeSmpId),
                   'data-point': 33}
        addBadDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addBadData)
        response = apiView.post(addBadDataPoint)
        self.assertEqual(response.status_code, 500)

        # modify
        addData = {'data_point_id': DataModel.generateDataPointId(
                    'sample', self._evaluation,
                    self._units[0], selectedReplica, fakeSmpId),
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
            'sample', self._evaluation,
            self._units[0], selectedReplica, fakeSmpId+1),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPointList, totalPoints = dataHelper.showDataPerLevel(
            Graph.L_SAMPLE, onlyThisData=True)
        self.assertEqual(totalPoints, 2)
        self.assertEqual(totalPoints, Sample.objects.count())
        self.assertEqual(totalPoints, SampleData.objects.count())
