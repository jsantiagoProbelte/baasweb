from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, Thesis, TrialDbInitialLoader, Replica
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory
from trialapp.fieldtrial_views import editNewFieldTrial, saveFieldTrial,\
    LayoutTrial, showFieldTrial


class FieldTrialViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_trialapp_index(self):
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertContains(response, 'Field Trials')
        self.assertContains(response, 'No Field Trial yet.')

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

        response = self.client.get(reverse('fieldtrial-list'))
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)

        thesis = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        response = self.client.get(reverse('fieldtrial-list'))
        self.assertNotContains(response, 'No Field Trial yet.')
        self.assertNotContains(response, 'Please define thesis first')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, '1 &#10000;</a>')  # Number thesis
        self.assertContains(response, '0 &#43;</a>')  # Number applications
        thesis.delete()
        fieldTrial.delete()

    def test_editfieldtrial(self):
        request_factory = RequestFactory()
        # request = request_factory.post('/fake-path', data={'name': u'Waldo'})
        request = request_factory.get('/edit_fieldtrial')
        response = editNewFieldTrial(request)
        self.assertContains(response, 'create-field-trial')
        self.assertContains(response, 'New Field Trial')
        self.assertNotContains(response, 'Edit Field Trial')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        fieldTrialData = TrialAppModelTest.FIELDTRIALS[0]
        request = request_factory.post('/save_fieldtrial', data=fieldTrialData)
        response = saveFieldTrial(request)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.name, fieldTrialData['name'])
        self.assertEqual(response.status_code, 302)

        request = request_factory.get(
            '/edit_fieldtrial/{}'.format(fieldTrial.id))
        response = editNewFieldTrial(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-field-trial')
        self.assertNotContains(response, 'New Field Trial')
        self.assertContains(response, 'Edit Field Trial')
        self.assertEqual(response.status_code, 200)

        newresponsible = 'Lobo'
        fieldTrialData['field_trial_id'] = fieldTrial.id
        fieldTrialData['responsible'] = newresponsible
        request = request_factory.post('/save_fieldtrial', data=fieldTrialData)
        print(fieldTrialData)
        response = saveFieldTrial(request, field_trial_id=fieldTrial.id)
        fieldTrial = FieldTrial.objects.get(name=fieldTrialData['name'])
        self.assertEqual(fieldTrial.responsible, newresponsible)
        self.assertEqual(response.status_code, 302)

        fieldTrial.delete()

    def test_layoutTrialSimplex(self):
        self.assertEqual(LayoutTrial.rangeToExplore(0), None)
        self.assertEqual(LayoutTrial.rangeToExplore(1), 0)

        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        self.assertGreater(fieldTrial.replicas_per_thesis, 0)
        self.assertEqual((3, 3),
                         LayoutTrial.calculateLayoutDim(fieldTrial, 2))
        self.assertEqual((3, 3),
                         LayoutTrial.calculateLayoutDim(fieldTrial, 2))
        self.assertEqual((3, 4),
                         LayoutTrial.calculateLayoutDim(fieldTrial, 3))

        thesis1 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        thesis2 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[1])

        Replica.createReplicas(thesis1, fieldTrial.replicas_per_thesis)
        Replica.createReplicas(thesis2, fieldTrial.replicas_per_thesis)

        replicas1 = Replica.getObjects(thesis1)
        self.assertEqual(len(replicas1),
                         fieldTrial.replicas_per_thesis)
        replicas2 = Replica.getObjects(thesis2)
        self.assertEqual(len(replicas2),
                         fieldTrial.replicas_per_thesis)
        self.assertTrue(LayoutTrial.isSameThesis(replicas1[0], replicas1[1]))
        self.assertFalse(LayoutTrial.isSameThesis(replicas1[0], replicas2[0]))
        self.assertFalse(LayoutTrial.isSameThesis(None, replicas2[0]))

        theses = Thesis.getObjects(fieldTrial)
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial,
            len(theses))

        self.assertEqual(len(deck), rows)
        self.assertEqual(len(deck[0]), columns)

        for i in range(0, rows):
            for j in range(0, columns):
                self.assertEqual(deck[i][j], None)
        # before assigning all elements are None
        deckShow = LayoutTrial.showLayout(fieldTrial, theses)
        for i in range(0, rows):
            for j in range(0, columns):
                self.assertEqual(deckShow[i][j], None)

        # Let's try to assign replicas one by one
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, replicas1[0]))
        self.assertEqual(deck[0][0].id, replicas1[0].id)
        self.assertEqual(replicas1[0].pos_x, 1)
        self.assertEqual(replicas1[0].pos_y, 1)

        self.assertFalse(LayoutTrial.tryAssign(deck, 0, 1, replicas1[1]))
        self.assertFalse(LayoutTrial.tryAssign(deck, 1, 0, replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 1, 1, replicas1[1]))
        self.assertTrue(LayoutTrial.tryAssign(deck, 2, 2, replicas1[1]))

        self.assertEqual(LayoutTrial.randomChooseItem([]), None)

        listReplicas = [replica for replica in replicas1]
        randomItem = LayoutTrial.randomChooseItem(listReplicas)
        self.assertEqual(randomItem.thesis.id, thesis1.id)
        self.assertEqual(len(listReplicas),
                         fieldTrial.replicas_per_thesis - 1)

    def test_layoutTrial2(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        thesis1 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        Replica.createReplicas(thesis1, fieldTrial.replicas_per_thesis)
        replicas1 = Replica.getObjects(thesis1)
        thesis2 = Thesis.create_Thesis(**TrialAppModelTest.THESIS[1])
        Replica.createReplicas(thesis2, fieldTrial.replicas_per_thesis)
        replicas2 = Replica.getObjects(thesis2)

        theses = Thesis.getObjects(fieldTrial)
        deck = LayoutTrial.showLayout(fieldTrial, theses)
        listReplicas = [replica for replica in replicas1]
        self.assertTrue(LayoutTrial.tryAssign(deck, 0, 0, replicas1[0]))
        self.assertFalse(LayoutTrial.assignReplica(listReplicas, deck, 0, 1))
        listReplicas = [replica for replica in replicas2]
        self.assertTrue(LayoutTrial.assignReplica(listReplicas, deck, 0, 1))
        self.assertEqual(deck[0][1].thesis.id, thesis2.id)
        self.assertEqual(deck[0][1].pos_x, 1)
        self.assertEqual(deck[0][1].pos_y, 2)

        deck = LayoutTrial.distributeLayout(fieldTrial, theses)

        # We should be able to find all the replicas
        for thesisReplicas in [replicas1, replicas2]:
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

        fieldTrial.delete()

    def test_showFieldTrial(self):
        fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])
        request_factory = RequestFactory()
        # request = request_factory.post('/fake-path', data={'name': u'Waldo'})
        request = request_factory.get(
            '/show_fieldtrial')
        response = showFieldTrial(request, field_trial_id=fieldTrial.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, fieldTrial.name)
