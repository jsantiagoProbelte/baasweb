from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, ProductThesis, Replica,\
                            TrialDbInitialLoader, Thesis
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.thesis_views import editThesis, saveThesis,\
    ManageProductToThesis, ManageReplicaToThesis, ThesisApi
from baaswebapp.tests.test_views import ApiRequestHelperTest


class ThesisViewsTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        FieldTrial.create_fieldTrial(**TrialAppModelTest.FIELDTRIALS[0])

    def test_editfieldtrial(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        request = self._apiFactory.get(
            'thesis-edit',
            data={'field_trial_id': fieldTrial.id})
        self._apiFactory.setUser(request)

        response = editThesis(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-thesis')
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        thesisData = TrialAppModelTest.THESIS[0]
        request = self._apiFactory.post('thesis-save',
                                        data=thesisData)
        self._apiFactory.setUser(request)
        response = saveThesis(request)
        thesis = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis.name, thesisData['name'])
        self.assertEqual(response.status_code, 302)

        # Editar y ver nuevo
        request = self._apiFactory.get(reverse(
            'thesis-edit', args=[fieldTrial.id]))
        self._apiFactory.setUser(request)
        response = editThesis(
            request,
            field_trial_id=fieldTrial.id,
            thesis_id=thesis.id)
        self.assertContains(response, 'create-thesis')
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, thesisData['name'])
        self.assertEqual(response.status_code, 200)

        newdescription = 'Thesis new description'
        thesisData['thesis_id'] = thesis.id
        thesisData['description'] = newdescription
        thesisData['number'] = thesis.number
        request = self._apiFactory.post('thesis-save',
                                        data=thesisData)
        self._apiFactory.setUser(request)
        response = saveThesis(request)
        thesis2 = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis2.description, newdescription)
        self.assertEqual(response.status_code, 302)

        # Lets add some products
        productData = {'product': 1, 'rate_unit': 1, 'rate': 6,
                       'thesis_id': thesis2.id}
        addProductThesisRequest = self._apiFactory.post(
            '/manage_product_to_thesis_api',
            data=productData)
        self._apiFactory.setUser(request)

        self.assertEqual(ProductThesis.objects.count(), 0)
        apiView = ManageProductToThesis()
        response = apiView.post(addProductThesisRequest)
        self.assertEqual(response.status_code, 200)
        thesisProducts = ProductThesis.objects.all()
        self.assertEqual(len(thesisProducts), 1)
        self.assertEqual(thesisProducts[0].thesis.name,
                         thesis2.name)

        deleteData = {'item_id': thesisProducts[0].id}
        deleteProductThesisRequest = self._apiFactory.post(
            'manage_product_to_thesis_api',
            data=deleteData)
        response = apiView.delete(deleteProductThesisRequest)
        self._apiFactory.setUser(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductThesis.objects.count(), 0)

        # Lets add a replica
        replicaData = {'thesis_id': thesis2.id}
        addReplicaThesisRequest = self._apiFactory.post(
            '/manage_replica_to_thesis_api',
            data=replicaData)

        expectedReplicas = fieldTrial.replicas_per_thesis
        self.assertEqual(Replica.objects.count(),
                         expectedReplicas)
        apiView = ManageReplicaToThesis()
        response = apiView.post(addReplicaThesisRequest)
        self._apiFactory.setUser(request)
        self.assertEqual(response.status_code, 200)
        thesisReplicas = Replica.objects.all()
        self.assertEqual(len(thesisReplicas),
                         expectedReplicas+1)
        self.assertEqual(thesisReplicas[0].thesis.name,
                         thesis2.name)

        deleteReplica = {'replica_id': thesisReplicas[0].id}
        deleteReplicaThesisRequest = self._apiFactory.post(
            'manage_replica_to_thesis_api',
            data=deleteReplica)
        self._apiFactory.setUser(request)
        response = apiView.delete(deleteReplicaThesisRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Replica.objects.count(), expectedReplicas)

    def test_ThesisApi(self):
        item = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        deletedId = item.id
        deleteData = {'item_id': deletedId}
        deleteRequest = self._apiFactory.post(
            'thesis_api',
            data=deleteData)
        apiView = ThesisApi()
        response = apiView.delete(deleteRequest)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Thesis.objects.filter(pk=deletedId).exists())
