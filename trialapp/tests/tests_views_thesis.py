from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis  # \ ProductThesis, Replica,
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.thesis_views import ThesisCreateView, ThesisUpdateView, ThesisApi
# ManageProductToThesis, ManageReplicaToThesis, , ThesisDeleteView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class ThesisViewsTest(TestCase):

    _apiFactory = None
    _fieldTrial = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

    def test_editfieldtrial(self):
        request = self._apiFactory.get(
            'thesis-add',
            data={'field_trial_id': self._fieldTrial.id})
        self._apiFactory.setUser(request)

        response = ThesisCreateView.as_view()(
            request,
            field_trial_id=self._fieldTrial.id)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        thesisData = TrialAppModelTest.THESIS[0].copy()
        thesisData['mode'] = '1'  # not mode_id , so it match the select form
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        thesis = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis.name, thesisData['name'])

        # Editar y ver nuevo
        request = self._apiFactory.get('thesis-update')
        self._apiFactory.setUser(request)
        response = ThesisUpdateView.as_view()(
            request,
            pk=thesis.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, thesisData['name'])

        newdescription = 'Thesis new description'
        thesisData['description'] = newdescription
        request = self._apiFactory.post('thesis-update',
                                        data=thesisData)
        self._apiFactory.setUser(request)
        response = ThesisUpdateView.as_view()(
            request,
            pk=thesis.id)
        thesis2 = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis2.description, newdescription)
        self.assertEqual(response.status_code, 302)

    # def test_addProductThesis():
    #     # Lets add some products
    #     productData = {'product': 1, 'rate_unit': 1, 'rate': 6,
    #                    'thesis_id': thesis2.id}
    #     addProductThesisRequest = self._apiFactory.post(
    #         '/manage_product_to_thesis_api',
    #         data=productData)
    #     self._apiFactory.setUser(request)

    #     self.assertEqual(ProductThesis.objects.count(), 0)
    #     apiView = ManageProductToThesis()
    #     response = apiView.post(addProductThesisRequest)
    #     self.assertEqual(response.status_code, 200)
    #     thesisProducts = ProductThesis.objects.all()
    #     self.assertEqual(len(thesisProducts), 1)
    #     self.assertEqual(thesisProducts[0].thesis.name,
    #                      thesis2.name)

    #     deleteData = {'item_id': thesisProducts[0].id}
    #     deleteProductThesisRequest = self._apiFactory.post(
    #         'manage_product_to_thesis_api',
    #         data=deleteData)
    #     response = apiView.delete(deleteProductThesisRequest)
    #     self._apiFactory.setUser(request)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(ProductThesis.objects.count(), 0)

    #     # Lets add a replica
    #     replicaData = {'thesis_id': thesis2.id}
    #     addReplicaThesisRequest = self._apiFactory.post(
    #         '/manage_replica_to_thesis_api',
    #         data=replicaData)

    #     expectedReplicas = fieldTrial.replicas_per_thesis
    #     self.assertEqual(Replica.objects.count(),
    #                      expectedReplicas)
    #     apiView = ManageReplicaToThesis()
    #     response = apiView.post(addReplicaThesisRequest)
    #     self._apiFactory.setUser(request)
    #     self.assertEqual(response.status_code, 200)
    #     thesisReplicas = Replica.objects.all()
    #     self.assertEqual(len(thesisReplicas),
    #                      expectedReplicas+1)
    #     self.assertEqual(thesisReplicas[0].thesis.name,
    #                      thesis2.name)

    #     deleteReplica = {'replica_id': thesisReplicas[0].id}
    #     deleteReplicaThesisRequest = self._apiFactory.post(
    #         'manage_replica_to_thesis_api',
    #         data=deleteReplica)
    #     self._apiFactory.setUser(request)
    #     response = apiView.delete(deleteReplicaThesisRequest)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(Replica.objects.count(), expectedReplicas)

    def test_ThesisApi(self):
        item = Thesis.create_Thesis(**TrialAppModelTest.THESIS[0])
        getRequest = self._apiFactory.post('thesis_api')
        apiView = ThesisApi()
        response = apiView.get(getRequest,
                               **{'thesis_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            item.getTitle())
