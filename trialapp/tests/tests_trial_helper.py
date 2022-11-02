from django.test import TestCase
from trialapp.models import FieldTrial, Thesis, TrialDbInitialLoader, Replica
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.fieldtrial_views import LayoutTrial


class TrialHelperTest(TestCase):

    _fieldTrial = None
    _thesis1 = None
    _thesis2 = None
    _replicas1 = None
    _replicas2 = None

    def setUp(self):
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
        self.assertEqual((3, 4),
                         LayoutTrial.calculateLayoutDim(self._fieldTrial, 3))

        self.assertEqual(len(self._replicas1),
                         self._fieldTrial.replicas_per_thesis)

        self.assertEqual(len(self._replicas2),
                         self._fieldTrial.replicas_per_thesis)
        self.assertTrue(LayoutTrial.isSameThesis(self._replicas1[0],
                                                 self._replicas1[1]))
        self.assertFalse(LayoutTrial.isSameThesis(self._replicas1[0],
                                                  self._replicas2[0]))
        self.assertFalse(LayoutTrial.isSameThesis(None, self._replicas2[0]))

        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            self._fieldTrial,
            len(self._theses))

        self.assertEqual(len(deck), rows)
        self.assertEqual(len(deck[0]), columns)

        for i in range(0, rows):
            for j in range(0, columns):
                self.assertEqual(deck[i][j], None)
        # before assigning all elements are None
        deckShow = LayoutTrial.showLayout(self._fieldTrial, self._theses)
        for i in range(0, rows):
            for j in range(0, columns):
                self.assertEqual(deckShow[i][j], None)

        # Let's try to assign replicas one by one
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, self._replicas1[0]))
        self.assertEqual(deck[0][0].id, self._replicas1[0].id)
        self.assertEqual(self._replicas1[0].pos_x, 1)
        self.assertEqual(self._replicas1[0].pos_y, 1)

        self.assertFalse(LayoutTrial.tryAssign(deck, 0, 1, self._replicas1[1]))
        self.assertFalse(LayoutTrial.tryAssign(deck, 1, 0, self._replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 1, 1, self._replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 2, 2, self._replicas1[1]))

        self.assertEqual(LayoutTrial.randomChooseItem([]), None)

        listReplicas = [replica for replica in self._replicas1]
        randomItem = LayoutTrial.randomChooseItem(listReplicas)
        self.assertEqual(randomItem.thesis.id, self._thesis1.id)
        self.assertEqual(len(listReplicas),
                         self._fieldTrial.replicas_per_thesis - 1)

    def test_layoutTrial2(self):
        deck = LayoutTrial.showLayout(self._fieldTrial, self._theses)
        listReplicas = [replica for replica in self._replicas1]
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, self._replicas1[0]))
        self.assertFalse(LayoutTrial.assignReplica(listReplicas, deck, 0, 1))
        listReplicas = [replica for replica in self._replicas2]
        self.assertTrue(LayoutTrial.assignReplica(listReplicas, deck, 0, 1))
        self.assertEqual(deck[0][1].thesis.id, self._thesis2.id)
        self.assertEqual(deck[0][1].pos_x, 1)
        self.assertEqual(deck[0][1].pos_y, 2)

        deck = LayoutTrial.distributeLayout(self._fieldTrial, self._theses)

        # We should be able to find all the replicas
        for thesisReplicas in [self._replicas1, self._replicas2]:
            for replica in thesisReplicas:
                found = False
                for row in deck:
                    for item in row:
                        if item is None:
                            found = True
                            continue
                        if replica.id == item.id:
                            found = True
                            break
                    if found:
                        break

                self.assertTrue(found)
