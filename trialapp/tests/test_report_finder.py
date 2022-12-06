from django.test import TestCase
from trialapp.models import FieldTrial, TrialDbInitialLoader
from trialapp.report_finder import ReportFinder


class TrialHelperTest(TestCase):

    def setUp(self):
        TrialDbInitialLoader.loadInitialTrialValues()

    def test_basics(self):
        testfile = __file__
        finder = ReportFinder()
        self.assertFalse(finder.doAction('', '', '')[0])
        self.assertFalse(finder.doAction(None, '', '')[0])
        text = 'field trial I love too ensayo de campo'
        self.assertTrue(finder.doDiscoverAction(text))
        # By default _keys are using the ones to discover
        self.assertTrue(finder.doAction(text, '', ''))

        importer = ReportFinder(ReportFinder.ACTION_IMPORTER)
        importer._actionDiscover = False
        importer._actionImporter = True
        importer.getTokensFieldTrial()
        self.assertFalse(importer.doAction(text, '', '')[1])
        aCrop = 'Strawberry'
        text = '{} is leker'.format(aCrop)
        self.assertFalse(importer.doAction(text, '', testfile)[1])

        ltext = text.lower()
        found, attributes = importer.scanAttributesFieldTrial(ltext)
        self.assertTrue(found)
        self.assertTrue('crop' in attributes)
        fakefielname = 'test_report_finder'
        self.assertTrue(importer.doAction(text.lower(),
                                          'test_report_finder',
                                          testfile)[1])
        fieldTrials = FieldTrial.getObjects()
        self.assertEqual(len(fieldTrials), 1)
        self.assertEqual(fieldTrials[0].crop.name, aCrop)
        self.assertEqual(fieldTrials[0].report_filename,
                         importer._baseDir + importer.ACTION_IMPORTER +
                         '/' + fakefielname)

    def test_badcovered(self):
        importer = ReportFinder('./trialapp/tests/fixtures')
        importer.run(['./trialapp/tests/fixtures/input'], importer=True)
