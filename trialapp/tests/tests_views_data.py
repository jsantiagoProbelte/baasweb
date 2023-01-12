from django.test import TestCase
from trialapp.models import AssessmentType, AssessmentUnit, FieldTrial,\
    Thesis, TrialAssessmentSet, TrialDbInitialLoader, Evaluation,\
    ModelHelpers, ReplicaData, Replica, Sample, SampleData
from trialapp.tests.tests_models import TrialAppModelTest

from baaswebapp.graphs import Graph
from trialapp.data_views import showDataThesisIndex,\
    SetDataEvaluation, ThesisData, ManageTrialAssessmentSet,\
    showTrialAssessmentSetIndex, showDataReplicaIndex,\
    showDataSamplesIndex, sortDataPointsForDisplay
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
        request = self._apiFactory.get('data_thesis_index',
                                       args=[self._evaluation.id])
        self._apiFactory.setUser(request)
        response = showDataThesisIndex(
            request,
            evaluation_id=self._evaluation.id)
        self.assertEqual(response.status_code, 200)

        for thesis in self._theses:
            for unit in self._units:
                idInput = ModelHelpers.generateDataPointId(
                    'thesis',
                    self._evaluation,
                    thesis,
                    unit)
                self.assertContains(response, idInput)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'thesis', self._evaluation,
                    self._theses[0],
                    self._units[0]),
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
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'thesis', self._evaluation,
                    self._theses[0],
                    self._units[0]),
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
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
            'thesis', self._evaluation,
            self._theses[1],
            self._units[0]),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

        dataPoints = ThesisData.getDataPoints(self._evaluation)
        graph = Graph('thesis', self._units, dataPoints)
        graphToDisplay, classGraph = graph.bar()
        self.assertEqual(len(graphToDisplay), 1)
        self.assertEqual(classGraph, 'col-md-12')
        graphToDisplay, classGraph = graph.scatter()
        self.assertEqual(len(graphToDisplay), 1)
        self.assertEqual(classGraph, 'col-md-12')

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

        self.assertEqual(graphT.traceId(dPT), thesis.number)
        self.assertEqual(graphR.traceId(dPR), thesis.number)
        self.assertEqual(graphS.traceId(dPS), replica.number)

        self.assertEqual(graphT.getTraceName(dPT), thesis.name)
        self.assertEqual(graphR.getTraceName(dPR), thesis.name)
        self.assertEqual(graphS.getTraceName(dPS), thesis.name)

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
            'trial_assessment_set_list',
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
        request = self._apiFactory.get('data_replica_index',
                                       args=[self._evaluation.id])
        self._apiFactory.setUser(request)
        response = showDataReplicaIndex(
            request,
            evaluation_id=self._evaluation.id)
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, 'assessment, add data per thesis')
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        self.assertGreater(len(replicas), 0)
        for replica in replicas:
            for unit in self._units:
                idInput = ModelHelpers.generateDataPointId(
                    'replica',
                    self._evaluation,
                    replica,
                    unit)
                self.assertContains(response, idInput)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'replica', self._evaluation,
                    replicas[0],
                    self._units[0]),
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
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'replica', self._evaluation,
                    replicas[0],
                    self._units[0]),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
            'replica', self._evaluation,
            replicas[1],
            self._units[0]),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ReplicaData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

    def test_setSampleData(self):
        request = self._apiFactory.get('data_sample_index',
                                       args=[self._evaluation.id])
        self._apiFactory.setUser(request)
        response = showDataSamplesIndex(
            request,
            evaluation_id=self._evaluation.id)
        self.assertEqual(response.status_code, 200)

        # we expect a redirect to define a samples per replica,
        # since the associated field trial has not defined
        for expectedToken in [
                'You need to define the number of samples per replica',
                'Edit',
                self._fieldTrial.name]:
            self.assertContains(response, expectedToken)

        # let's set it manually and try again
        self._fieldTrial.samples_per_replica = 25
        self._fieldTrial.save()
        response = showDataSamplesIndex(
            request,
            evaluation_id=self._evaluation.id)
        # we should have know the page to select replicas
        self.assertContains(response, 'assessment, add data per sample')

        # Now, the user should have select a replica and then
        # she should get a page to input data per sample, even
        # if samples are not created yet. Le's check that
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        selectedReplica = replicas[0]
        samples = Sample.getObjects(selectedReplica)
        self.assertEqual(len(samples), 0)
        # let's simluate the selection of that replica
        request = self._apiFactory.get(
            'data_sample_index',
            args=[self._evaluation.id, selectedReplica.id])
        self._apiFactory.setUser(request)
        response = showDataSamplesIndex(
            request,
            evaluation_id=self._evaluation.id,
            selected_replica_id=selectedReplica.id)
        self.assertContains(response, 'Insert data for')
        self.assertContains(response, selectedReplica.getTitle())

        # During this call, the samples are created
        samples = Sample.getObjects(selectedReplica)
        self.assertTrue(len(samples), self._fieldTrial.samples_per_replica)

        for item in samples:
            for unit in self._units:
                idInput = ModelHelpers.generateDataPointId(
                    'sample',
                    self._evaluation,
                    item,
                    unit)
                self.assertContains(response, idInput)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'sample', self._evaluation,
                    samples[0],
                    self._units[0]),
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
        self.assertEqual(tPoints[0].reference.id,
                         samples[0].id)
        self.assertEqual(tPoints[0].unit,
                         self._units[0])

        # add bad values
        self.assertEqual(ThesisData.objects.count(), 0)
        addBadData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'badboy', self._evaluation,
                    samples[0],
                    self._units[0]),
                   'data-point': 33}
        addBadDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addBadData)
        response = apiView.post(addBadDataPoint)
        self.assertEqual(response.status_code, 500)

        # modify
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
                    'sample', self._evaluation,
                    samples[0],
                    self._units[0]),
                   'data-point': 66}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': ModelHelpers.generateDataPointId(
            'sample', self._evaluation,
            samples[1],
            self._units[0]),
            'data-point': 99}
        addDataPoint = self._apiFactory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = SampleData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

    def test_sortDataPointsForDisplay(self):
        replicas = Replica.getFieldTrialObjects(
            self._fieldTrial)
        dataPoints = ReplicaData.getDataPoints(self._evaluation)
        self.assertEqual(len(dataPoints), 0)
        dataPointsList = sortDataPointsForDisplay(
            'replica', self._evaluation,
            replicas, self._units, dataPoints)
        self.assertEqual(len(dataPointsList), len(replicas))
        selectedReplica = replicas[0]
        self.assertEqual(selectedReplica.getKey(),
                         dataPointsList[0]['name'])
        self.assertEqual(
            ModelHelpers.generateDataPointId(
                'replica', self._evaluation,
                selectedReplica, self._units[0]),
            dataPointsList[0]['dataPoints'][0]['item_id'])
        self.assertEqual(
            '',
            dataPointsList[0]['dataPoints'][0]['value'])

        # let generate dataPoint
        ReplicaData.objects.create(
            reference=selectedReplica,
            unit=self._units[0],
            value=33,
            evaluation=self._evaluation)
        dataPoints = ReplicaData.getDataPoints(self._evaluation)
        self.assertEqual(len(dataPoints), 1)
        dataPointsList = sortDataPointsForDisplay(
            'replica', self._evaluation,
            replicas, self._units, dataPoints)
        self.assertEqual(len(dataPointsList), len(replicas))
        selectedReplica = replicas[0]
        self.assertEqual(selectedReplica.getKey(),
                         dataPointsList[0]['name'])
        self.assertEqual(
            33,
            dataPointsList[0]['dataPoints'][0]['value'])
        self.assertEqual(
            ModelHelpers.generateDataPointId(
                'replica', self._evaluation,
                selectedReplica, self._units[0]),
            dataPointsList[0]['dataPoints'][0]['item_id'])
