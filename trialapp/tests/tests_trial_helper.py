from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica, StatusTrial
from baaswebapp.tests.tests_helpers import TrialTestData
from trialapp.trial_helper import LayoutTrial, TrialPermission
from baaswebapp.tests.tests_helpers import ApiRequestHelperTest, UserStub
from trialapp.thesis_views import SetReplicaPosition
from django.utils.translation import gettext_lazy as _
from trialapp.trial_views import TrialApi
from trialapp.fieldtrial_views import DownloadTrial


class TrialHelperTest(TestCase):
    _trial = None
    _thesis1 = None
    _thesis2 = None
    _replicas1 = None
    _replicas2 = None
    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._trial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        self._thesis1 = Thesis.createThesis(**TrialTestData.THESIS[0])
        self._thesis2 = Thesis.createThesis(**TrialTestData.THESIS[1])
        self._theses = Thesis.getObjects(self._trial)

        Replica.createReplicas(self._thesis1,
                               self._trial.repetitions)
        Replica.createReplicas(self._thesis2,
                               self._trial.repetitions)
        self._replicas1 = Replica.getObjects(self._thesis1)
        self._replicas2 = Replica.getObjects(self._thesis2)

    def test_distributeLayout(self):
        # let´s mess it and arrange it
        deck = LayoutTrial.showLayout(self._trial, None, self._theses)

        replicaM = Replica.objects.get(pk=self._replicas1[0].id)
        self.assertEqual(replicaM.pos_x, 0)
        self.assertEqual(replicaM.pos_y, 0)
        replicaM.pos_x = 0
        replicaM.pos_y = 0
        replicaM.save()

        deck = LayoutTrial.showLayout(
            self._trial, None, self._theses)

        for row in deck:
            for item in row:
                self.assertNotEqual(
                    item['replica_id'],
                    replicaM.id)

        rows, columns = LayoutTrial.calculateLayoutDim(
            self._trial, len(self._theses))

        replicaZ = Replica.objects.get(pk=self._replicas1[1].id)
        self.assertNotEqual(replicaZ, rows+1)
        self.assertNotEqual(replicaZ, columns+1)
        replicaZ.pos_x = rows+1
        replicaZ.pos_y = columns+1
        replicaZ.save()
        deck = LayoutTrial.showLayout(
            self._trial, None, self._theses)
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
        deck = LayoutTrial.showLayout(self._trial, None, self._theses)
        replica2 = deck[theReplica2.pos_y-1][theReplica2.pos_x-1]
        self.assertEqual(theReplica2.id, replica2['replica_id'])

        # TODO replica1 = deck[theReplica1.pos_y-1][theReplica1.pos_x-1]
        # TODO self.assertEqual(theReplica1.id, replica1['replica_id'])

    def test_headerLayout(self):
        headers = LayoutTrial.headerLayout(self._trial)
        self.assertEqual(len(headers), self._trial.repetitions)
        self.assertEqual(headers[0]['name'], 'A')

    def assertPermissions(self, trial, user, discoverable, readible,
                          downloadable, editable):
        trialP = TrialPermission(trial, user).getPermisions()
        self.assertEqual(trialP[TrialPermission.DISCOVERABLE], discoverable)
        self.assertEqual(trialP[TrialPermission.READIBLE], readible)
        self.assertEqual(trialP[TrialPermission.DOWNLOADABLE], downloadable)
        self.assertEqual(trialP[TrialPermission.EDITABLE], editable)

    def test_permisions(self):
        trial = self._trial
        ownerName = self._trial.responsible

        ownerInternal = UserStub(ownerName, False, True)
        ownerExternal = UserStub(ownerName, False, False)
        admin = UserStub('GOD', True, True)
        notOwnerInternal = UserStub('Ziggy', False, True)
        notOwnerExternal = UserStub('Ziggy', False, False)
        open = StatusTrial.PROTOCOL
        finished = StatusTrial.DONE

        # discoverable, readible, downloadable, editable

        # Trial Not Finished, no public, no favorable
        trial.status_trial = open
        trial.public = False
        trial.favorable = False
        self.assertPermissions(trial, notOwnerExternal,
                               False, False, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, True)
        self.assertPermissions(trial, notOwnerInternal,
                               True, False, False, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, False, True)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Not Finished, public, no favorable
        trial.status_trial = open
        trial.public = True
        trial.favorable = False
        self.assertPermissions(trial, notOwnerExternal,
                               False, False, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, True)
        self.assertPermissions(trial, notOwnerInternal,
                               True, False, False, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, False, True)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Not Finished, public, favorable
        trial.status_trial = open
        trial.public = True
        trial.favorable = True
        self.assertPermissions(trial, notOwnerExternal,
                               False, False, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, True)
        self.assertPermissions(trial, notOwnerInternal,
                               True, False, False, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, False, True)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Finished, no public, no favorable
        trial.status_trial = finished
        trial.public = False
        trial.favorable = False
        self.assertPermissions(trial, notOwnerExternal,
                               False, False, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, False)
        self.assertPermissions(trial, notOwnerInternal,
                               True, True, False, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, False, False)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Finished, no public, favorable
        trial.status_trial = finished
        trial.public = False
        trial.favorable = True
        self.assertPermissions(trial, notOwnerExternal,
                               False, False, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, False)
        self.assertPermissions(trial, notOwnerInternal,
                               True, True, True, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, True, False)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Finished, public, no favorable
        trial.status_trial = finished
        trial.public = True
        trial.favorable = False
        self.assertPermissions(trial, notOwnerExternal,
                               True, True, False, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, False, False)
        self.assertPermissions(trial, notOwnerInternal,
                               True, True, False, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, False, False)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

        # Trial Finished, public, no favorable
        trial.status_trial = finished
        trial.public = True
        trial.favorable = True
        self.assertPermissions(trial, notOwnerExternal,
                               True, True, True, False)
        self.assertPermissions(trial, ownerExternal,
                               True, True, True, False)
        self.assertPermissions(trial, notOwnerInternal,
                               True, True, True, False)
        self.assertPermissions(trial, ownerInternal,
                               True, True, True, False)
        self.assertPermissions(trial, admin,
                               True, True, True, True)

    def test_errormessage(self):
        trial = self._trial
        self._trial.responsible = "Ziggy"
        self._trial.save()
        user = UserStub("Ziggy", False, True)
        trialP = TrialPermission(trial, user)

        trialP._permissions[TrialPermission.READIBLE] = True
        trialP._permissions[TrialPermission.DISCOVERABLE] = False
        self.assertEqual(
            trialP.getError(),
            _('You do not have permission to access this trial'))

        trialP._permissions[TrialPermission.READIBLE] = False
        trialP._permissions[TrialPermission.DISCOVERABLE] = True
        self.assertEqual(
            trialP.getError(),
            _('You do not have permission to access this trial'))

        request = self._apiFactory.get('trial_api')
        self._apiFactory.setUser(request)
        response = TrialApi.as_view()(request, pk=self._trial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, _('You do not have permission to access this trial'))

        trialP._permissions[TrialPermission.READIBLE] = True
        trialP._permissions[TrialPermission.DISCOVERABLE] = True
        trialP._permissions[TrialPermission.DOWNLOADABLE] = False
        self.assertEqual(
            trialP.getError(),
            _('You do not have permission to download this trial'))
        # make it readible and discorable but not downloadable
        self._trial.status_trial = StatusTrial.DONE
        self._trial.public = True
        self._trial.favorable = False
        self._trial.save()
        request = self._apiFactory.get('trial_api')
        self._apiFactory.setUser(request)
        response = DownloadTrial.as_view()(request, pk=self._trial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, _('You do not have permission to download this trial'))

        response = trialP.renderError(request, 'Esto no es un error')
        self.assertContains(
            response, 'Esto no es un error')

        trialP._permissions[TrialPermission.DOWNLOADABLE] = True
        trialP._permissions[TrialPermission.EDITABLE] = False
        self.assertEqual(trialP.getError(),
                         _('You do not have permission to edit this trial'))

        trialP._permissions[TrialPermission.EDITABLE] = True
        self.assertEqual(trialP.getError(),
                         _('No limitations on permissions'))
