from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from catalogue.models import Product, ProductVariant, Batch, Treatment, \
    RateUnit, UNTREATED
from trialapp.models import FieldTrial, Thesis, Replica, \
                            ApplicationMode, TreatmentThesis
from baaswebapp.tests.tests_helpers import TrialTestData
from trialapp.thesis_views import\
    ThesisCreateView, ThesisUpdateView, ThesisApi, ThesisDeleteView, \
    ThesisListView, TreatmentThesisSetView, TreatmentThesisDeleteView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class ThesisViewsTest(TestCase):

    _apiFactory = None
    _trial = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._trial = FieldTrial.createTrial(**TrialTestData.TRIALS[0])
        self._untreated = Treatment.objects.get(name=UNTREATED)

    def test_editfieldtrial(self):
        request = self._apiFactory.get(
            'thesis-add',
            data={'field_trial_id': self._trial.id})
        self._apiFactory.setUser(request)

        response = ThesisCreateView.as_view()(
            request,
            field_trial_id=self._trial.id)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        thesisData = TrialTestData.THESIS[0].copy()
        thesisData['treatment'] = self._untreated.id
        thesisData['mode'] = '1'  # not mode_id , so it match the select form
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        self.assertEqual(response.status_code, 302)
        thesis = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis.name, thesisData['name'])

        # Editar y ver nuevo
        thesisData.pop('treatment')
        request = self._apiFactory.get('thesis-update',
                                       data=thesisData)
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

    def test_addTreatmentThesis(self):
        thesisData = TrialTestData.THESIS[0].copy()
        thesisData['treatment'] = self._untreated.id
        thesisData['mode'] = '1'  # not mode_id , so it match the select form
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        self.assertEqual(response.status_code, 302)
        thesis = Thesis.objects.get(name=thesisData['name'])

        # Lets add some products
        product = Product.objects.get(id=2)
        variant = ProductVariant.objects.create(name='A variant',
                                                product=product)
        rateUnit = RateUnit.objects.create(name='unit')
        batch = Batch.objects.create(
            **{'name': 'bbbbbbb', 'serial_number': 'sn', 'rate': 1,
               'rate_unit': rateUnit, 'product_variant': variant})
        treatment = Treatment.objects.create(
            **{"name": 'pppp', 'rate': 1, 'rate_unit': rateUnit,
                "batch": batch})

        # TODO: Let;s add some ThesisTreatment
        token = 'treatment_thesis'
        setTreatView = TreatmentThesisSetView
        deleteView = TreatmentThesisDeleteView
        theClass = TreatmentThesis
        url_add = token+'-add'
        url_delete = token+'-delete'
        createGet = self._apiFactory.get(url_add)
        self._apiFactory.setUser(createGet)
        response = setTreatView.as_view()(
            createGet, thesis_id=thesis.id)
        self.assertTrue(response.status_code, 200)

        data = {'product': product.id}
        setProductGet = self._apiFactory.get(url_add, data=data)
        self._apiFactory.setUser(setProductGet)
        response = setTreatView.as_view()(
            setProductGet, thesis_id=thesis.id)
        self.assertTrue(response.status_code, 200)
        # no existe todavia
        self.assertFalse(theClass.objects.filter(
            treatment=treatment).exists())

        data = {'treatment': treatment.id,
                'thesis_id': thesis.id}
        setTreatmentGet = self._apiFactory.get(url_add, data=data)
        self._apiFactory.setUser(setTreatmentGet)
        response = setTreatView.as_view()(
            setTreatmentGet, thesis_id=thesis.id)
        self.assertTrue(response.status_code, 302)
        theItem = theClass.objects.get(treatment=treatment)

        deleteGet = self._apiFactory.get(url_delete)
        self._apiFactory.setUser(deleteGet)
        response = deleteView.as_view()(deleteGet,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 200)
        self.assertTrue(theClass.objects.filter(treatment=treatment).exists())

        deletePost = self._apiFactory.delete(url_delete)
        self._apiFactory.setUser(deletePost)
        response = deleteView.as_view()(deletePost,
                                        pk=theItem.id)
        self.assertTrue(response.status_code, 302)
        self.assertFalse(theClass.objects.filter(treatment=treatment).exists())

    def test_thesis_api(self):
        # Creating thesis , but not with all attributres
        thesisData = TrialTestData.THESIS[0].copy()
        thesisData['treatment'] = self._untreated.id
        request = self._apiFactory.post('thesis-add', thesisData)
        self._apiFactory.setUser(request)
        response = ThesisCreateView.as_view()(
            request, field_trial_id=self._trial.id)
        self.assertEqual(response.status_code, 302)
        item = Thesis.objects.get(name=thesisData['name'])

        # when thesis is created, it is expected that its replicas are
        # also created
        expectedReplicas = self._trial.repetitions
        self.assertEqual(Replica.objects.count(),
                         expectedReplicas)

        getRequest = self._apiFactory.get('thesis_api')
        self._apiFactory.setUser(getRequest)
        response = ThesisApi.as_view()(getRequest, pk=item.id)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            item.getTitle())

        # Let's call thesis list
        getRequest = self._apiFactory.get('thesis-list')
        self._apiFactory.setUser(getRequest)
        response = ThesisListView.as_view()(
            getRequest, **{'field_trial_id': self._trial.id})
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
        for thesis in TrialTestData.THESIS:
            copiedData = thesis.copy()
            copiedData['mode'] = ApplicationMode.objects.get(pk=1)
            theThesis = Thesis.createThesis(**copiedData)
            theThesisId = theThesis.id
        # numberThesis = Thesis.getObjects(self._trial).count()
        api = ThesisApi()
        # We do not care which one to use
        api._thesis = Thesis.objects.get(id=theThesisId)

        thesisVolume = api.getThesisVolume()
        self.assertTrue('Missing Data: Volume' in thesisVolume['value'])
        appVolume = 100
        self._trial.application_volume = appVolume
        self._trial.save()

        api._thesis = Thesis.objects.get(id=theThesisId)
        thesisVolume = api.getThesisVolume()
        self.assertTrue('Missing Data: Gross area' in thesisVolume['value'])
        grossArea = 100
        self._trial.gross_surface = grossArea
        self._trial.save()

        api._thesis = Thesis.objects.get(id=theThesisId)
        thesisVolume = api.getThesisVolume()
        # litres = grossArea * appVolume * self._trial.repetitions
        # surfacePerThesis = (numberThesis * self._trial.repetitions * 10000)
        # thesisVolumeV = litres / surfacePerThesis
        # unit = 'L'
        # rounding = 2
        # if thesisVolumeV < 1.0:
        #     thesisVolumeV = thesisVolumeV * 1000
        #     unit = 'mL'
        #     rounding = 0
        self.assertEqual(thesisVolume['value'], '500 mL')
        # {} {}'.format(round(thesisVolumeV, rounding), unit))
