from django.test import TestCase
from trialapp.trial_analytics import TrialAnalytics, SNK_Table, Abbott
from baaswebapp.tests.tests_helpers import DataGenerator


class TrialAnalyticsTest(TestCase):
    _expected = {
        '15 DA-E': {
            1: [97.33, 'a', 0],
            2: [97.73, 'a', 0],
            3: [97.47, 'a', 0],
            4: [98.67, 'a', 0],
            5: [86.13, 'c', -12],
            6: [96.53, 'a', -1],
            7: [97.33, 'a', 0],
            8: [98.00, 'a', 0],
            9: [91.60, 'b', -6],
            10: [23.73, 'd', -76]}}

    def setUp(self):
        pass

    def test_analytics(self):
        generator = DataGenerator()
        debug = False
        for trial in generator._fieldTrials:
            ta = TrialAnalytics(generator._fieldTrials[trial])
            debug = False if debug else True
            ta.calculateAnalytics(debug=debug)

    def test_tableSNK(self):
        self.assertEqual(
            SNK_Table.qCriticalSNK(0, 1),
            None)
        self.assertEqual(
            SNK_Table.qCriticalSNK(121, 2),
            SNK_Table.qCritical__0_05['inf'][0])
        self.assertEqual(
            SNK_Table.qCriticalSNK(120, 2),
            SNK_Table.qCritical__0_05[120][0])
        self.assertEqual(
            SNK_Table.qCriticalSNK(85, 2),
            SNK_Table.qCritical__0_05[60][0])
        self.assertEqual(
            SNK_Table.qCriticalSNK(15, 20),
            SNK_Table.qCritical__0_05[15][18])
        self.assertEqual(
            SNK_Table.qCriticalSNK(15, 1),
            None)
        values = {15: 15, 120: 120, 115: 60, 121: 'inf'}
        for df in values:
            row = values[df]
            lastK = len(SNK_Table.qCritical__0_05[row]) + 2
            self.assertEqual(
                SNK_Table.qCriticalSNK(df, lastK-1),
                SNK_Table.qCritical__0_05[row][lastK-3])
            self.assertEqual(
                SNK_Table.qCriticalSNK(df, lastK),
                SNK_Table.qCritical__0_05[row][-1])
            self.assertEqual(
                SNK_Table.qCriticalSNK(df, lastK+1),
                SNK_Table.qCritical__0_05[row][-1])

    def test_abbott(self):
        self.assertEqual(Abbott.do(80, 100), -20)
        self.assertEqual(Abbott.do(100, 80), 25)

        self.assertEqual(Abbott(0, {0: 0, 1: 80, 2: 100}).run(), None)
        self.assertEqual(Abbott(0, {1: 80, 2: 100}).run(), None)
        self.assertEqual(Abbott(0, {0: 80, 1: 100, 2: 160, 3: 40}).run(),
                         {1: 25, 2: 100, 3: -50})
