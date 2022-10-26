from django.test import TestCase
from django.urls import reverse
from trialapp.models import FieldTrial, TrialDbInitialLoader, Thesis
from trialapp.tests.tests_models import TrialAppModelTest
from django.test import RequestFactory

from trialapp.thesis_views import editThesis, saveThesis
# from trialapp.thesis_views import editThesis


class ThesisViewsTest(TestCase):

    def setUp(cls):
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
        request = request_factory.post('/save_thesis',
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
        request = request_factory.post('/save_fieldtrial',
                                       data=thesisData)
        response = saveThesis(request, thesis_id=thesis.id)
        thesis2 = Thesis.objects.get(name=thesisData['name'])
        self.assertEqual(thesis2.description, newdescription)
        self.assertEqual(response.status_code, 302)
