from django.test import TestCase
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Application
from trialapp.tests.tests_models import TrialAppModelTest
from trialapp.application_views import\
    ApplicationCreateView, ApplicationUpdateView, ApplicationApi,\
    ApplicationDeleteView, ApplicationListView
from baaswebapp.tests.test_views import ApiRequestHelperTest


class ApplicationViewsTest(TestCase):

    _apiFactory = None
    _fieldTrial = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()
        TrialDbInitialLoader.loadInitialTrialValues()
        self._fieldTrial = FieldTrial.create_fieldTrial(
            **TrialAppModelTest.FIELDTRIALS[0])

    def test_editfieldtrial(self):
        request = self._apiFactory.get(
            'application-add',
            data={'field_trial_id': self._fieldTrial.id})
        self._apiFactory.setUser(request)

        response = ApplicationCreateView.as_view()(
            request,
            field_trial_id=self._fieldTrial.id)
        self.assertContains(response, 'New')
        self.assertNotContains(response, 'Edit')
        self.assertEqual(response.status_code, 200)

        # Create one field trial
        applicationData = TrialAppModelTest.APPLICATION[0].copy()
        request = self._apiFactory.post('application-add', applicationData)
        self._apiFactory.setUser(request)
        response = ApplicationCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        application = Application.objects.get(
            app_date=applicationData['app_date'])
        self.assertEqual(application.daa, 0)
        self.assertEqual(application.getName(), 'DAA-0')

        # Editar y ver nuevo
        request = self._apiFactory.get('application-update')
        self._apiFactory.setUser(request)
        response = ApplicationUpdateView.as_view()(
            request,
            pk=application.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'New')
        self.assertContains(response, 'Edit')
        self.assertContains(response, applicationData['comment'])

        newdescription = 'Application new description'
        applicationData['comment'] = newdescription
        request = self._apiFactory.post('application-update',
                                        data=applicationData)
        self._apiFactory.setUser(request)
        response = ApplicationUpdateView.as_view()(
            request,
            pk=application.id)
        application2 = Application.objects.get(
            app_date=applicationData['app_date'])
        self.assertEqual(application2.comment, newdescription)
        self.assertEqual(response.status_code, 302)

    def test_application_api(self):
        # Creating application , but not with all attributres
        applicationData = TrialAppModelTest.APPLICATION[0]
        request = self._apiFactory.post('application-add', applicationData)
        self._apiFactory.setUser(request)
        response = ApplicationCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item = Application.objects.get(app_date=applicationData['app_date'])

        getRequest = self._apiFactory.get('application_api')
        apiView = ApplicationApi()
        response = apiView.get(getRequest,
                               **{'application_id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            item.comment)

        # Let's create another one
        applicationData2 = TrialAppModelTest.APPLICATION[1]
        request = self._apiFactory.post('application-add', applicationData2)
        self._apiFactory.setUser(request)
        response = ApplicationCreateView.as_view()(
            request, field_trial_id=self._fieldTrial.id)
        self.assertEqual(response.status_code, 302)
        item2 = Application.objects.get(app_date=applicationData2['app_date'])
        daa = (item2.app_date - item.app_date).days
        self.assertTrue(item2.daa, daa)

        # Let's call application list
        getRequest = self._apiFactory.get('application-list')
        self._apiFactory.setUser(getRequest)
        response = ApplicationListView.as_view()(
            getRequest, **{'field_trial_id': self._fieldTrial.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, item.comment)
        self.assertContains(response, item.getName())
        self.assertContains(response, item2.getName())

        deleteRequest = self._apiFactory.delete('application-delete')
        self._apiFactory.setUser(deleteRequest)
        deletedId = item.id
        response = ApplicationDeleteView.as_view()(deleteRequest,
                                                   pk=deletedId)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Application.objects.filter(pk=deletedId).exists())
