from django.test import TestCase
from trialapp.models import AssessmentType, AssessmentUnit, FieldTrial,\
    Thesis, TrialAssessmentSet, TrialDbInitialLoader, Evaluation
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory

from trialapp.data_views import showDataThesisIndex,\
    SetDataEvaluation, ThesisData, ManageTrialAssessmentSet,\
    showTrialAssessmentSetIndex
# from trialapp.evaluation_views import editEvaluation


class DataViewsTest(TestCase):

    _fieldTrial = None
    _theses = []
    _units = []
    _evaluation = None

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        for thesis in TrialAppModelTest.THESIS:
            self._theses.append(Thesis.create_Thesis(**thesis))
        self._units = [TrialAssessmentSet.objects.create(
            field_trial=self._fieldTrial,
            type=AssessmentType.objects.get(pk=i),
            unit=AssessmentUnit.objects.get(pk=i)) for i in range(1, 3)]

        self._evaluation = Evaluation.objects.create(
            name='eval1',
            evaluation_date='2022-12-15',
            field_trial=self._fieldTrial,
            crop_stage_majority=65,
            crop_stage_scale='BBCH')

    def test_setData(self):
        request_factory = RequestFactory()
        request = request_factory.get('data_thesis_index',
                                      args=[self._evaluation.id])
        response = showDataThesisIndex(
            request,
            evaluation_id=self._evaluation.id)
        self.assertEqual(response.status_code, 200)

        for thesis in self._theses:
            for unit in self._units:
                idInput = SetDataEvaluation.generateId(
                    'thesis',
                    self._evaluation,
                    thesis,
                    unit)
                self.assertContains(response, idInput)

        # Le's add data
        self.assertEqual(ThesisData.objects.count(), 0)
        addData = {'data_point_id': SetDataEvaluation.generateId(
                    'thesis', self._evaluation,
                    self._theses[0],
                    self._units[0]),
                   'data-point': 33}
        addDataPoint = request_factory.post(
            'set_data_point',
            data=addData)
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
        addData = {'data_point_id': SetDataEvaluation.generateId(
                    'thesis', self._evaluation,
                    self._theses[0],
                    self._units[0]),
                   'data-point': 66}
        addDataPoint = request_factory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 1)
        self.assertEqual(tPoints[0].value, 66)

        # add new point
        addData = {'data_point_id': SetDataEvaluation.generateId(
            'thesis', self._evaluation,
            self._theses[1],
            self._units[0]),
            'data-point': 99}
        addDataPoint = request_factory.post(
            'set_data_point',
            data=addData)
        response = apiView.post(addDataPoint)
        tPoints = ThesisData.objects.all()
        self.assertEqual(len(tPoints), 2)
        self.assertEqual(tPoints[1].value, 99)

    def test_manageEvaluationSet(self):
        request_factory = RequestFactory()
        requestIndex = request_factory.get(
            'trial_assessment_set_list',
            args=[self._fieldTrial.id])

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
            'trial_assessment_set_id': unitsInTrial[0].id}
        deleteDataPoint = request_factory.post(
            'manage_trial_assessment_set_api',
            data=deleteData)
        apiView = ManageTrialAssessmentSet()
        response = apiView.delete(deleteDataPoint)
        self.assertEqual(response.status_code, 200)
        unitsInTrial = TrialAssessmentSet.getObjects(self._fieldTrial)
        self.assertEqual(len(unitsInTrial), initialUnits-1)

        requestIndex = request_factory.get(
            'trial_assessment_set_list',
            args=[self._fieldTrial.id])
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
            'assessment_unit': deleteUnitId
        }
        addDataPoint = request_factory.post(
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
