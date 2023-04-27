from django.test import TestCase
from labapp.labtrial_views import DataLabHelper


class LabTrialDataTest(TestCase):

    _apiFactory = None

    TEST_DATA = {'020323': {
        'dipel': {
            'data': [[0, 24], [3, 23], [7, 24], [13, 23], [20, 24], [24, 24]],
            'ld50': 1.76},
        'bf27': {
            'data': [[0, 24], [3, 24], [6, 24], [12, 24], [18, 24], [24, 24]],
            'ld50': 2.28},
        '16sc': {
            'data': [[0, 24], [4, 24], [7, 24], [14, 24], [20, 24], [24, 24]],
            'ld50': 1.63},
        'F036': {
            'data': [[0, 24], [1, 24], [3, 24], [7, 24], [13, 24], [20, 24]],
            'ld50': 5.36},
        'F024': {
            'data': [[0, 24], [1, 24], [2, 24], [5, 24], [11, 24], [18, 24]],
            'ld50': 8.21},
        }}

    def setUp(self):
        self._helper = DataLabHelper(None)

    def test_datastatstest(self):
        # load data into pandas dataframe
        dosis = [0, 0.25, 0.74, 2.22, 6.66, 20]
        ocurrences = [[0, 24], [3, 23], [7, 24], [13, 23], [20, 24], [24, 24]]
        ld50 = self._helper.calculateLD50(ocurrences, dosis)
        print('{}: ld50:{} esperado:{}'.format('test', round(ld50, 3), 1.76))

    def test_datastats(self):
        dosis = [0, 0.25, 0.74, 2.22, 6.66, 20]
        for label in self.TEST_DATA['020323']:
            ocurrences = self.TEST_DATA['020323'][label]['data']
            expected = self.TEST_DATA['020323'][label]['ld50']
            ld50 = self._helper.calculateLD50(ocurrences, dosis)

            print('{}: ld50:{} esperado:{} error:{}%'.format(label,
                  round(ld50, 2),
                  expected, round(100*(ld50-expected) / expected, 2)))
