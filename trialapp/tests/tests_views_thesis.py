from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, ProductThesis, Replica,\
                            ApplicationMode
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.thesis_views import ThesisCreateView, ThesisUpdateView,\
                                  ThesisApi, ManageProductToThesis,\
                                  ThesisDeleteView,\
                                  ThesisListView
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

    def test_addProductThesis(self):
        thesisData = TrialAppModelTest.THESIS[0].copy()
        thesisData['mode'] = '1'  # not mode_id , so it match the select form
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        thesis = Thesis.objects.get(name=thesisData['name'])

        # Lets add some products
        productData = {'product': 1, 'rate_unit': 1, 'rate': 6,
                       'thesis_id': thesis.id}
        addProductThesisRequest = self._apiFactory.post(
            '/manage_product_to_thesis_api',
            data=productData)
        self._apiFactory.setUser(addProductThesisRequest)

        self.assertEqual(ProductThesis.objects.count(), 0)
        apiView = ManageProductToThesis()
        response = apiView.post(addProductThesisRequest)
        self.assertEqual(response.status_code, 200)
        thesisProducts = ProductThesis.objects.all()
        self.assertEqual(len(thesisProducts), 1)
        self.assertEqual(thesisProducts[0].thesis.name,
                         thesis.name)

        deleteData = {'item_id': thesisProducts[0].id}
        deleteProductThesisRequest = self._apiFactory.post(
            'manage_product_to_thesis_api',
            data=deleteData)
        response = apiView.delete(deleteProductThesisRequest)
        self._apiFactory.setUser(deleteProductThesisRequest)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductThesis.objects.count(), 0)

    def test_thesis_api(self):
        # Creating thesis , but not with all attributres
        thesisData = TrialAppModelTest.THESIS[0]
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Thesis.objects.get(name=thesisData['name'])

        # when thesis is created, it is expected that its replicas are
        # also created
        expectedReplicas = self._fieldTrial.replicas_per_thesis
        self.assertEqual(Replica.objects.count(),
                         expectedReplicas)

        getRequest = self._apiFactory.post('thesis_api')
        apiView = ThesisApi()
        response = apiView.get(getRequest,
                               **{'thesis_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            item.getTitle())

        # Let's call thesis list
        getRequest = self._apiFactory.get('thesis-list')
        self._apiFactory.setUser(getRequest)
        response = ThesisListView.as_view()(
            getRequest, **{'field_trial_id': self._fieldTrial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.name)

        deleteRequest = self._apiFactory.delete('thesis-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = item.id
        response = ThesisDeleteView.as_view()(deleteRequest,
                                              pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Thesis.objects.filter(pk=deletedId).exists())

    def test_ThesisVolume(self):
        theThesis = None
        theThesisId = None
        for thesis in TrialAppModelTest.THESIS:
            copiedData = thesis.copy()
            copiedData['mode'] = ApplicationMode.objects.get(pk=1)
            theThesis = Thesis.create_Thesis(**copiedData)
            theThesisId = theThesis.id
        # numberThesis = Thesis.getObjects(self._fieldTrial).count()
        api = ThesisApi()
        # We do not care which one to use
        api._thesis = Thesis.objects.get(id=theThesisId)

        thesisVolume = api.getThesisVolume()
        self.assertTrue('Missing Data: Volume' in thesisVolume['value'])
        appVolume = 100
        self._fieldTrial.application_volume = appVolume
        self._fieldTrial.save()

        api._thesis = Thesis.objects.get(id=theThesisId)
        thesisVolume = api.getThesisVolume()
        self.assertTrue('Missing Data: Net area' in thesisVolume['value'])
        netArea = 100
        self._fieldTrial.net_surface = netArea
        self._fieldTrial.save()

        api._thesis = Thesis.objects.get(id=theThesisId)
        thesisVolume = api.getThesisVolume()
        # litres = netArea * appVolume * self._fieldTrial.replicas_per_thesis
        # surfacePerThesis = (numberThesis * self._fieldTrial.blocks * 10000)
        # thesisVolumeV = litres / surfacePerThesis
        # unit = 'L'
        # rounding = 2
        # if thesisVolumeV < 1.0:
        #     thesisVolumeV = thesisVolumeV * 1000
        #     unit = 'mL'
        #     rounding = 0
        self.assertEqual(thesisVolume['value'], '667 mL')
        # {} {}'.format(round(thesisVolumeV, rounding), unit))
