from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, ProductThesis, Replica,\
                            TrialDbInitialLoader, Thesis
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory

from trialapp.thesis_views import editThesis, saveThesis,\
    ManageProductToThesis, ManageReplicaToThesis
# from trialapp.thesis_views import editThesis


class ThesisViewsTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()
        FieldTrial.create_fieldTrial(**TrialAppModelTest.FIELDTRIALS[0])

    def test_thesis_emply_list(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        response = self.client.get(reverse(
            'thesis-list', args=[fieldTrial.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Thesis')
        self.assertContains(response, fieldTrial.name)
        self.assertContains(response, 'No Thesis yet.')

    def test_editfieldtrial(self):
        fieldTrial = FieldTrial.objects.get(
            name=TrialAppModelTest.FIELDTRIALS[0]['name'])
        request_factory = RequestFactory()
        request = request_factory.get('/edit_thesis')
        response = editThesis(request, field_trial_id=fieldTrial.id)
        self.assertContains(response, 'create-thesis')
        self.assertContains(response, 'New Thesis')
        self.assertNotContains(response, 'Edit Thesis')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        thesisData = TrialAppModelTest.THESIS[0]
        request = request_factory.post('thesis-save',
                                       data=thesisData)
        response = saveThesis(request)
        thesis = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis.name, thesisData['name'])
        self.assertEqual(response.status_code, 302)

        # Editar y ver nuevo
        request = request_factory.get(
            '/edit_thesis/{}'.format(fieldTrial.id))
        response = editThesis(
            request,
            field_trial_id=fieldTrial.id,
            thesis_id=thesis.id)
        self.assertContains(response, 'create-thesis')
        self.assertNotContains(response, 'New Thesis')
        self.assertContains(response, 'Edit Thesis')
        self.assertContains(response, thesisData['name'])
        self.assertEqual(response.status_code, 200)

        newdescription = 'Thesis new description'
        thesisData['thesis_id'] = thesis.id
        thesisData['description'] = newdescription
        request = request_factory.post('thesis-save',
                                       data=thesisData)
        response = saveThesis(request)
        thesis2 = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis2.description, newdescription)
        self.assertEqual(response.status_code, 302)

        # Lets add some products
        productData = {'product': 1, 'rate_unit': 1, 'rate': 6,
                       'thesis_id': thesis2.id}
        addProductThesisRequest = request_factory.post(
            '/manage_product_to_thesis_api',
            data=productData)

        self.assertEqual(ProductThesis.objects.count(),
                         0)
        apiView = ManageProductToThesis()
        response = apiView.post(addProductThesisRequest)
        self.assertEqual(response.status_code, 200)
        thesisProducts = ProductThesis.objects.all()
        self.assertEqual(len(thesisProducts),
                         1)
        self.assertEqual(thesisProducts[0].thesis.name,
                         thesis2.name)

        deleteData = {'product_thesis_id': thesisProducts[0].id}
        deleteProductThesisRequest = request_factory.post(
            'manage_product_to_thesis_api',
            data=deleteData)
        response = apiView.delete(deleteProductThesisRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductThesis.objects.count(),
                         0)

        # Lets add a replica
        replicaData = {'thesis_id': thesis2.id}
        addReplicaThesisRequest = request_factory.post(
            '/manage_replica_to_thesis_api',
            data=replicaData)

        expectedReplicas = fieldTrial.replicas_per_thesis
        self.assertEqual(Replica.objects.count(),
                         expectedReplicas)
        apiView = ManageReplicaToThesis()
        response = apiView.post(addReplicaThesisRequest)
        self.assertEqual(response.status_code, 200)
        thesisReplicas = Replica.objects.all()
        self.assertEqual(len(thesisReplicas),
                         expectedReplicas+1)
        self.assertEqual(thesisReplicas[0].thesis.name,
                         thesis2.name)

        deleteReplica = {'replica_id': thesisReplicas[0].id}
        deleteReplicaThesisRequest = request_factory.post(
            'manage_replica_to_thesis_api',
            data=deleteReplica)
        response = apiView.delete(deleteReplicaThesisRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Replica.objects.count(),
                         expectedReplicas)
