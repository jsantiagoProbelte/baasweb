from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.trial_helper import LayoutTrial
from trialapp.fieldtrial_views import reshuffle_blocks
from baaswebapp.tests.test_views import ApiRequestHelperTest


class TrialHelperTest(TestCase):

    _fieldTrial = None
    _thesis1 = None
    _thesis2 = None
    _replicas1 = None
    _replicas2 = None
    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        self._thesis1 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        self._thesis2 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[1])
        self._theses = Thesis.getObjects(self._fieldTrial)

        Replica.createReplicas(self._thesis1,
                               self._fieldTrial.replicas_per_thesis)
        Replica.createReplicas(self._thesis2,
                               self._fieldTrial.replicas_per_thesis)
        self._replicas1 = Replica.getObjects(self._thesis1)
        self._replicas2 = Replica.getObjects(self._thesis2)

    def test_layoutTrialSimplex(self):
        self.assertEqual(LayoutTrial.rangeToExplore(0), None)
        self.assertEqual(LayoutTrial.rangeToExplore(1), 0)

        self.assertGreater(self._fieldTrial.replicas_per_thesis, 0)
        self.assertEqual((3, 3),
                         LayoutTrial.calculateLayoutDim(self._fieldTrial, 2))
        self.assertEqual((3, 3),
                         LayoutTrial.calculateLayoutDim(self._fieldTrial, 2))
        self.assertEqual((4, 3),
                         LayoutTrial.calculateLayoutDim(self._fieldTrial, 3))

        self.assertEqual(len(self._replicas1),
                         self._fieldTrial.replicas_per_thesis)

        self.assertEqual(len(self._replicas2),
                         self._fieldTrial.replicas_per_thesis)
        self.assertTrue(LayoutTrial.isSameThesis({
            'number': self._replicas1[1].thesis_id},
            self._replicas1[1]))
        self.assertFalse(LayoutTrial.isSameThesis({
            'number': 33},
             self._replicas2[0]))
        self.assertFalse(LayoutTrial.isSameThesis(None, self._replicas2[0]))

        deck, (blocks, columns) = LayoutTrial.computeInitialLayout(
            self._fieldTrial,
            len(self._theses))

        self.assertEqual(len(deck), blocks)
        self.assertEqual(len(deck[0]), columns)

        for i in range(0, blocks):
            for j in range(0, columns):
                self.assertEqual(deck[i][j],
                                 LayoutTrial.setDeckCell(None, None))
        # before assigning all elements are None
        deckShow = LayoutTrial.showLayout(self._fieldTrial, None, self._theses)
        for i in range(0, blocks):
            for j in range(0, columns):
                self.assertEqual(
                    deckShow[i][j],
                    LayoutTrial.setDeckCell(None, None))

        self.assertFalse(LayoutTrial.tryAssign(deck, 0, 0, None))

        # Let's try to assign replicas one by one
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, self._replicas1[0]))
        self.assertEqual(deck[0][0]['number'], self._thesis1.id)
        self.assertEqual(self._replicas1[0].pos_x, 1)
        self.assertEqual(self._replicas1[0].pos_y, 1)

        # let try to assign the same
        self.assertFalse(LayoutTrial.tryAssign(deck, 0, 0, self._replicas1[1]))

        self.assertFalse(LayoutTrial.tryAssign(deck, 0, 1, self._replicas1[1]))
        self.assertFalse(LayoutTrial.tryAssign(deck, 1, 0, self._replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 1, 1, self._replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 2, 2, self._replicas1[1]))

    def test_distributeLayout(self):
        deck = LayoutTrial.showLayout(self._fieldTrial, None, self._theses)
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, self._replicas1[0]))
        self.assertEqual(self._replicas1[0].pos_x, 1)
        self.assertEqual(self._replicas1[0].pos_y, 1)

        deck = LayoutTrial.distributeLayout(self._fieldTrial)
        # We should be able to find all the replicas
        for thesisReplicas in [self._replicas1, self._replicas2]:
            for replica in thesisReplicas:
                found = False
                for row in deck:
                    for item in row:
                        if item is None:
                            found = True
                            continue
                        if replica.id == item['replica_id']:
                            found = True
                            break
                    if found:
                        break
                self.assertTrue(found)

        # Try with a small set
        self._fieldTrial.replicas_per_thesis = 0
        self.assertEqual(
            LayoutTrial.distributeLayout(self._fieldTrial), None)

    def test_distributeLayout2(self):
        # let´s mess it and arrange it
        deck = LayoutTrial.distributeLayout(self._fieldTrial)

        replicaM = Replica.objects.get(pk=self._replicas1[0].id)
        self.assertNotEqual(replicaM.pos_x, 0)
        self.assertNotEqual(replicaM.pos_y, 0)
        replicaM.pos_x = 0
        replicaM.pos_y = 0
        replicaM.save()

        deck = LayoutTrial.showLayout(
            self._fieldTrial, None, self._theses)

        for row in deck:
            for item in row:
                self.assertNotEqual(
                    item['replica_id'],
                    replicaM.id)

        rows, columns = LayoutTrial.calculateLayoutDim(
            self._fieldTrial, len(self._theses))

        replicaZ = Replica.objects.get(pk=self._replicas1[1].id)
        self.assertNotEqual(replicaZ, rows+1)
        self.assertNotEqual(replicaZ, columns+1)
        replicaZ.pos_x = rows+1
        replicaZ.pos_y = columns+1
        replicaZ.save()
        deck = LayoutTrial.showLayout(
            self._fieldTrial, None, self._theses)
        for row in deck:
            for item in row:
                self.assertNotEqual(
                    item['replica_id'],
                    replicaZ.id)

        # let´s change it
        request = self._apiFactory.get(
            'field_trial_api',
            data={'field_trial_id': self._fieldTrial.id})
        self._apiFactory.setUser(request)
        response = reshuffle_blocks(
            request, field_trial_id=self._fieldTrial.id)
        self.assertTrue(response.status_code, 200)
        _replicas1 = Replica.getObjects(self._thesis1)
        self.assertNotEqual(_replicas1[0].pos_x, 0)
        self.assertNotEqual(_replicas1[0].pos_y, 0)
        self.assertNotEqual(_replicas1[1].pos_x, rows+1)
        self.assertNotEqual(_replicas1[1].pos_y, columns+1)

    def test_headerLayout(self):
        headers = LayoutTrial.headerLayout(self._fieldTrial)
        self.assertEqual(len(headers), self._fieldTrial.blocks)
        self.assertEqual(headers[0]['name'], 'A')
