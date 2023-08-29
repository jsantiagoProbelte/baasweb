from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica, TrialStatus
from trialapp.tests.tests_helpers import TrialAppModelData
from trialapp.trial_helper import LayoutTrial, TrialPermission
from baaswebapp.tests.test_views import ApiRequestHelperTest
from trialapp.thesis_views import SetReplicaPosition


class UserStub:
    username = None
    is_superuser = None

    def __init__(self, name, superUser):
        self.username = name
        self.is_superuser = superUser


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
            **TrialAppModelData.FIELDTRIALS[0])
        self._thesis1 = Thesis.create_Thesis(**TrialAppModelData.THESIS[0])
        self._thesis2 = Thesis.create_Thesis(**TrialAppModelData.THESIS[1])
        self._theses = Thesis.getObjects(self._fieldTrial)

        Replica.createReplicas(self._thesis1,
                               self._fieldTrial.replicas_per_thesis)
        Replica.createReplicas(self._thesis2,
                               self._fieldTrial.replicas_per_thesis)
        self._replicas1 = Replica.getObjects(self._thesis1)
        self._replicas2 = Replica.getObjects(self._thesis2)

    def test_distributeLayout(self):
        # let´s mess it and arrange it
        deck = LayoutTrial.showLayout(self._fieldTrial, None, self._theses)

        replicaM = Replica.objects.get(pk=self._replicas1[0].id)
        self.assertEqual(replicaM.pos_x, 0)
        self.assertEqual(replicaM.pos_y, 0)
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

    def test_settingPosition(self):
        #  let's put first replica in position 3,2
        theReplica1 = Replica.objects.get(pk=self._replicas1[0].id)
        x1 = 3
        y1 = 2
        addData = {'replica_position': theReplica1.id}
        addDataPoint = self._apiFactory.post(
            'set-replica-position',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        apiView = SetReplicaPosition()
        response = apiView.post(addDataPoint, x1, y1, 0)
        self.assertTrue(response.status_code, 302)
        theReplica1 = Replica.objects.get(id=theReplica1.id)
        self.assertEqual(theReplica1.pos_x, x1)
        self.assertEqual(theReplica1.pos_y, y1)

        # Add another
        x2 = 1
        y2 = 3
        theReplica2 = Replica.objects.get(pk=self._replicas2[0].id)
        addData = {'replica_position': theReplica2.id}
        addDataPoint = self._apiFactory.post(
            'set-replica-position',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint, x2, y2, 0)
        self.assertTrue(response.status_code, 302)
        theReplica2 = Replica.objects.get(id=theReplica2.id)
        self.assertEqual(theReplica2.pos_x, x2)
        self.assertEqual(theReplica2.pos_y, y2)

        # Interchange
        addData = {'replica_position': theReplica1.id}
        addDataPoint = self._apiFactory.post(
            'set-replica-position',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint, x2, y2, theReplica2.id)
        self.assertTrue(response.status_code, 302)
        theReplica2 = Replica.objects.get(id=theReplica2.id)
        theReplica1 = Replica.objects.get(id=theReplica1.id)
        self.assertEqual(theReplica1.pos_x, x2)
        self.assertEqual(theReplica1.pos_y, y2)
        self.assertEqual(theReplica2.pos_x, x1)
        self.assertEqual(theReplica2.pos_y, y1)

        # Remove replica from position
        addData = {'replica_position': ''}
        addDataPoint = self._apiFactory.post(
            'set-replica-position',
            data=addData)
        self._apiFactory.setUser(addDataPoint)
        response = apiView.post(addDataPoint, x1, y1, theReplica2.id)
        self.assertTrue(response.status_code, 302)
        theReplica2 = Replica.objects.get(id=theReplica2.id)
        self.assertEqual(theReplica2.pos_x, 0)
        self.assertEqual(theReplica2.pos_y, 0)

        theReplica2.pos_x = x1
        theReplica2.pos_y = y1
        theReplica2.save()
        deck = LayoutTrial.showLayout(self._fieldTrial, None, self._theses)
        replica2 = deck[theReplica2.pos_y-1][theReplica2.pos_x-1]
        self.assertEqual(theReplica2.id, replica2['replica_id'])

        replica1 = deck[theReplica1.pos_y-1][theReplica1.pos_x-1]
        self.assertEqual(theReplica1.id, replica1['replica_id'])

    def test_headerLayout(self):
        headers = LayoutTrial.headerLayout(self._fieldTrial)
        self.assertEqual(len(headers), self._fieldTrial.blocks)
        self.assertEqual(headers[0]['name'], 'A')

    def test_permisions(self):
        trial = self._fieldTrial
        owner = self._fieldTrial.responsible

        trialP = TrialPermission(trial, UserStub(owner, False)).getPermisions()
        self.assertTrue(trialP[TrialPermission.ADD_DATA])
        self.assertTrue(trialP[TrialPermission.EDIT])

        trialP = TrialPermission(trial, UserStub('GOD', False)).getPermisions()
        self.assertFalse(trialP[TrialPermission.ADD_DATA])
        self.assertFalse(trialP[TrialPermission.EDIT])

        trialP = TrialPermission(trial, UserStub('GOD', True)).getPermisions()
        self.assertTrue(trialP[TrialPermission.ADD_DATA])
        self.assertTrue(trialP[TrialPermission.EDIT])

        finishStatus = TrialStatus.objects.get(name=TrialStatus.FINISHED)
        trial.trial_status = finishStatus
        trial.save()
        trialP = TrialPermission(trial, UserStub('GOD', True)).getPermisions()
        self.assertFalse(trialP[TrialPermission.ADD_DATA])
        self.assertTrue(trialP[TrialPermission.EDIT])

        trialP = TrialPermission(trial, UserStub(owner, False)).getPermisions()
        self.assertFalse(trialP[TrialPermission.ADD_DATA])
        self.assertTrue(trialP[TrialPermission.EDIT])
