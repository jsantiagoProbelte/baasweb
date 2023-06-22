from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.data_models import ReplicaData, Assessment
from trialapp.trial_analytics import TrialAnalytics


class TrialAnalyticsTest(TestCase):
    _fieldTrials = {}
    _assessments = {}
    _expected = {
        '15 DA-E': {
            1: [97.33, 'a', 0],
            2: [97.73, 'a', 0],
            3: [97.47, 'a', 0],
            4: [98.67, 'a', 0],
            5: [86.13, 'c', -12],
            6: [96.53, 'a', -1],
            7: [97.33, 'a', 0],
            8: [98.00, 'a', 0],
            9: [91.60, 'b', -6],
            10: [23.73, 'd', -76]}}

    dataAssessment = {
            '15 DA-E': {
                1: [97.60, 97.20, 97.20],
                2: [98.40, 97.20, 97.60],
                3: [97.60, 97.60, 97.20],
                4: [98.80, 98.40, 98.80],
                5: [85.20, 85.20, 88.00],
                6: [97.20, 96.00, 96.40],
                7: [97.60, 97.60, 96.80],
                8: [97.60, 97.60, 98.80],
                9: [93.20, 88.80, 92.80],
                10: [31.20, 21.20, 18.80]},
            'PageTest': {
                1: [164, 172, 177, 156, 195],
                2: [178, 191, 182, 185, 177],
                3: [175, 193, 171, 163, 176],
                4: [155, 166, 164, 170, 168]},
            '12 DA-D': {
                1: [54.5, 38.9, 17.5, 28.6],
                2: [54.5, 69.4, 62.5, 100],
                3: [0, 81.7, 18.2, 60.7],
                4: [75.2, 8.3, 47.5, 0],
                5: [0, 0, 0, 0]}}

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        # Create as many as trials as assessments to try
        # different conditions
        assessList = list(self.dataAssessment.keys())
        num_assessments = len(assessList)
        for i in range(num_assessments):
            theses = {}
            replicas = {}
            trialData = TrialAppModelTest.FIELDTRIALS[0].copy()
            trialData['name'] = f"trial{i}"
            trial = FieldTrial.create_fieldTrial(**trialData)
            self._fieldTrials[i] = trial

            assName = assessList[i]
            assInfo = {
                'name': assName,
                'assessment_date': '2022-05-14',
                'rate_type_id': 1,
                'part_rated': 'LEAF, P',
                'crop_stage_majority': '89, 89, 89',
                'field_trial_id': trial.id}
            self._assessments[assName] = Assessment.objects.create(**assInfo)
            assId = self._assessments[assName].id
            assData = self.dataAssessment[assName]
            num_thesis = len(assData.keys())
            num_replicas = len(assData[1])
            for j in range(1, num_thesis+1):
                thesis = Thesis.objects.create(
                    name='{}'.format(j),
                    number=j,
                    field_trial_id=trial.id)
                theses[j] = thesis
                replicas[j] = Replica.createReplicas(thesis, num_replicas)

            for tId in range(1, num_thesis+1):
                for index in range(num_replicas):
                    ReplicaData.objects.create(
                        assessment_id=assId,
                        reference_id=replicas[tId][index],
                        value=assData[tId][index])

    def test_analytics(self):
        for trial in self._fieldTrials:
            ta = TrialAnalytics(self._fieldTrials[trial])
            ta.calculateAnalytics(debug=True)
