import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from scipy.stats import bartlett, levene
import numpy as np
from trialapp.models import Replica, Thesis
from trialapp.data_models import ReplicaData, Assessment


class SNK_Table:
    qCritical__0_05 = {
        1: [17.969, 26.976, 32.819, 37.082, 40.408, 43.119, 45.397, 47.357, 49.071, 50.592, 51.957, 53.194, 54.323, 55.361, 56.320, 57.212, 58.044, 58.824, 59.558],  # noqa: E501
        2: [6.085, 8.331, 9.798, 10.881, 11.734, 12.435, 13.027, 13.539, 13.988, 14.389, 14.749, 15.076, 15.375, 15.650, 15.905, 16.143, 16.365, 16.573, 16.769],  # noqa: E501
        3: [4.501, 5.910, 6.825, 7.502, 8.037, 8.478, 8.852, 9.177, 9.462, 9.717, 39.946, 10.155, 10.346, 10.522, 10.686, 10.838, 10.980, 11.114, 11.240],  # noqa: E501
        4: [3.926, 5.040, 5.757, 6.287, 6.706, 7.053, 7.347, 7.602, 7.826, 8.027, 8.208, 8.373, 8.524, 8.664, 8.793, 8.914, 9.027, 39.133, 9.233],  # noqa: E501
        5: [3.635, 4.602, 5.218, 5.673, 6.033, 6.330, 6.582, 6.801, 6.995, 7.167, 7.323, 7.466, 7.596, 7.716, 7.828, 7.932, 8.030, 8.122, 8.208],  # noqa: E501
        6: [3.460, 4.339, 4.896, 5.305, 5.628, 5.895, 6.122, 6.319, 6.493, 6.649, 6.789, 6.917, 7.034, 7.143, 7.244, 7.338, 7.426, 7.508, 7.586],  # noqa: E501
        7: [3.344, 4.165, 4.681, 5.060, 5.359, 5.606, 5.815, 5.997, 6.158, 6.302, 6.431, 6.550, 6.658, 6.759, 6.852, 6.939, 7.020, 7.097, 7.169],  # noqa: E501
        8: [3.261, 4.041, 4.529, 4.886, 5.167, 5.399, 5.596, 5.767, 5.918, 6.053, 6.175, 6.287, 6.389, 6.483, 6.571, 6.653, 6.729, 6.801, 6.869],  # noqa: E501
        9: [3.199, 3.948, 4.415, 4.755, 5.024, 5.244, 5.432, 5.595, 5.738, 5.867, 5.983, 6.089, 6.186, 6.276, 6.359, 6.437, 6.510, 6.579, 6.643],  # noqa: E501
        10: [3.151, 3.877, 4.327, 4.654, 4.912, 5.124, 5.304, 5.460, 5.598, 5.722, 5.833, 5.935, 6.028, 6.114, 6.19, 6.269, 6.339, 6.405, 6.467],  # noqa: E501
        11: [3.113, 3.820, 4.256, 4.574, 4.823, 5.028, 5.202, 5.353, 5.486, 5.605, 5.713, 5.811, 5.901, 5.984, 6.062, 6.134, 6.202, 6.265, 6.325],  # noqa: E501
        12: [3.081, 3.773, 4.199, 4.508, 4.750, 4.950, 5.119, 5.265, 5.395, 5.510, 5.615, 5.710, 5.797, 5.878, 5.953, 6.023, 6.089, 6.151, 6.209],  # noqa: E501
        13: [3.055, 3.734, 4.151, 4.453, 4.690, 4.884, 5.049, 5.192, 5.318, 5.431, 5.533, 5.625, 5.711, 5.789, 5.862, 5.931, 5.995, 6.055, 6.112],  # noqa: E501
        14: [3.033, 3.701, 4.111, 4.407, 4.639, 4.829, 4.990, 5.130, 5.253, 5.364, 5.463, 5.554, 5.637, 5.714, 5.785, 5.852, 5.915, 5.973, 6.029],  # noqa: E501
        15: [3.014, 3.673, 4.076, 4.367, 4.595, 4.782, 4.940, 5.077, 5.198, 5.306, 5.403, 5.492, 5.574, 5.649, 5.719, 5.785, 5.846, 5.94, 5.958],  # noqa: E501
        16: [2.998, 3.649, 4.046, 4.333, 4.557, 4.741, 4.896, 5.031, 5.150, 5.256, 5.352, 5.439, 5.519, 5.593, 5.662, 5.726, 5.786, 5.843, 5.896],  # noqa: E501
        17: [2.984, 3.628, 4.020, 4.303, 4.524, 4.705, 4.858, 4.991, 5.108, 5.212, 5.306, 5.392, 5.471, 5.544, 5.612, 5.675, 5.734, 5.790, 5.842],  # noqa: E501
        18: [2.971, 3.609, 3.997, 4.276, 4.494, 4.673, 4.824, 4.955, 5.071, 5.173, 5.266, 5.351, 5.429, 5.501, 5.567, 5.629, 5.688, 5.743, 5.794],  # noqa: E501
        19: [2.960, 3.593, 3.977, 4.253, 4.468, 4.645, 4.794, 4.924, 5.037, 5.139, 5.231, 5.314, 5.391, 5.462, 5.528, 5.589, 5.647, 5.701, 5.752],  # noqa: E501
        20: [2.950, 3.578, 3.958, 4.232, 4.445, 4.620, 4.768, 4.895, 5.008, 5.108, 5.199, 5.282, 5.357, 5.427, 5.492, 5.553, 5.610, 5.663, 5.714],  # noqa: E501
        21: [2.941, 3.565, 3.92, 4.213, 4.424, 4.597, 4.743, 4.870, 4.981, 5.081, 5.170, 5.252, 5.327, 5.396, 5.460, 5.520, 5.576, 5.629, 5.679],  # noqa: E501
        22: [2.933, 3.553, 3.927, 4.196, 4.405, 4.577, 4.722, 4.847, 4.957, 5.056, 5.144, 5.225, 5.299, 5.368, 5.431, 5.491, 5.546, 5.599, 5.648],  # noqa: E501
        23: [2.926, 3.542, 3.914, 4.180, 4.388, 4.558, 4.702, 4.826, 4.935, 5.033, 5.121, 5.201, 5.274, 5.342, 5.405, 5.464, 5.519, 5.571, 5.620],  # noqa: E501
        24: [2.919, 3.532, 3.901, 4.166, 4.373, 4.541, 4.684, 4.807, 4.915, 5.012, 5.099, 5.179, 5.251, 5.319, 5.381, 5.439, 5.494, 5.545, 5.5],  # noqa: E501
        25: [2.913, 3.523, 3.890, 4.153, 4.358, 4.526, 4.667, 4.789, 4.897, 4.993, 5.079, 5.158, 5.230, 5.297, 5.359, 5.417, 5.471, 5.522, 5.570],  # noqa: E501
        30: [2.89, 3.49, 3.85, 4.10, 4.30, 4.46, 4.60, 4.72, 4.82],
        40:	[2.86, 3.44, 3.79, 4.04, 4.23, 4.39, 4.52, 4.63, 4.73],
        60:	[2.83, 3.40, 3.74, 3.98, 4.16, 4.31, 4.44, 4.55, 4.65],
        120: [2.80,	3.36, 3.68, 3.92, 4.10, 4.24, 4.36, 4.47, 4.56],
        'inf': [2.77, 3.31, 3.63, 3.86, 4.03, 4.17, 4.29, 4.39, 4.47]}

    @classmethod
    def qCriticalSNK(cls, df, p):
        # rows are df, degrees of freedom
        # columsn are groups, first column is 2 and last is 20
        if df < 1:
            return None
        elif df > 120:
            row = cls.qCritical__0_05['inf']
        elif df not in cls.qCritical__0_05:
            return cls.qCriticalSNK(df-1, p)
        else:
            row = cls.qCritical__0_05[df]
        if p < 2:
            return None
        index = p - 2
        if len(row) <= index:
            index = -1
        return row[index]


class TrialAnalytics:
    def __init__(self, trial):
        self._trial = trial
        self._replicas = Replica.getDict(self._trial)
        self._thesis = {item.id: item.number
                        for item in Thesis.getObjects(trial)}

    def calculateAnalytics(self, debug=False):
        for assessment in Assessment.getObjects(self._trial):
            analytics = AssessmentAnalytics(assessment, len(self._thesis),
                                            debug=debug)
            analytics.analyse(self._replicas)


class AssessmentAnalytics:
    _assessment = None
    _anova_table = None
    _abbott = None
    _replicaData = {}
    _groups = []
    _sig_diff = {}
    _sig_letters = {}
    _data_groups = []
    _debug = False
    _statsText = ''
    _snk = {}
    _result = {}
    _indexThesis = {}
    _thesisGroupTag = None

    def __init__(self, assessment, num_thesis,
                 isSampleData=False,
                 debug=False):
        self._assessment = assessment
        # significant lettters
        self._sig_letters = self.genSigLetter(num_thesis)
        self._sig_diff = {i: [] for i in range(num_thesis)}
        self._debug = debug
        self._replicaData = {}
        self._data = []
        self._means = None
        self._std_devs = None
        self._n_samples = None
        self._result = {}
        self._indexThesis = {}
        if isSampleData:
            self._thesisGroupTag = 'reference__replica__thesis__number'
        else:
            self._thesisGroupTag = 'reference__thesis__number'

    def analyse(self, replicas, dataReplica=None):
        self.prepareData(replicas, dataReplica=dataReplica)
        if self._data and len(self._means) > 1:
            self.anova()
            self.SNK()
            self.barlett()
            self.levene()

    def getReplicaDataAndGroup(self, replicas):
        for thesisId in replicas:
            dataV = ReplicaData.objects.filter(
                assessment=self._assessment,
                reference_id__in=replicas[thesisId])
            data = [float(item.value) for item in dataV]
            self._replicaData[thesisId] = data

    def groupReplicaData(self, dataReplica):
        for item in dataReplica:
            thesisNum = item[self._thesisGroupTag]
            value = float(item['value'])
            if thesisNum not in self._replicaData:
                self._replicaData[thesisNum] = []
            self._replicaData[thesisNum].append(value)

    def prepareData(self, replicas, dataReplica=None):
        means = []
        std_devs = []
        lens = []
        self._groups = []
        self._data_groups = []
        if dataReplica is None:
            self.getReplicaDataAndGroup(replicas)
        else:
            self.groupReplicaData(dataReplica)
        index = 0
        for thesisNum in self._replicaData:
            # Sometimes we do not have all thesis data
            # we need to remember the order
            self._indexThesis[index] = thesisNum
            index += 1
            data = self._replicaData[thesisNum]
            self._data += data
            self._data_groups.append(data)
            mean = np.mean(data)
            means.append(mean)
            std = np.std(data)
            std_devs.append(std)
            length = len(data)
            lens.append(length)
            self._groups += ['__{}__'.format(thesisNum)] * length
            self._result[thesisNum] = {
                'mean': round(mean, 2),
                'std': round(std, 2)}

        # Combine all groups into one array
        self._means = np.array(means)
        self._std_devs = np.array(std_devs)
        self._n_samples = np.array(lens)
        if self._debug:
            print(f">>> Ass[{self._assessment.name}]")

    def anova(self):
        # Create a pandas DataFrame
        df = pd.DataFrame({'Groups': self._groups, 'Data': self._data})
        # Perform one-way ANOVA
        model = ols('Data ~ Groups', data=df).fit()
        self._anova_table = sm.stats.anova_lm(model, typ=2)
        self._statsText += "<p class='txt-regular-16'>ANOVA test</p>"
        self._statsText += self._anova_table.transpose().to_html(
            classes='table stats-table no-border')
        if self._debug:
            print(self._anova_table)

    def getStats(self):
        return {
            'stats': self._statsText,
            'out': self._result,
            'abbott': self._abbott}

    def genSigLetter(self, num_thesis):
        return [chr(num) for num in range(97, 97 + num_thesis + 1)]

    def sortMeans(self):
        num_thesis = len(self._means)
        thesisMeans = {i: self._means[i] for i in range(num_thesis)}
        sorted_dict = [k for k, v in sorted(thesisMeans.items(),
                                            key=lambda item: item[1],
                                            reverse=True)]
        return sorted_dict, num_thesis

    def calculateSwitQ(self, num_thesis, n_samples):
        # See page 93
        swit = np.sqrt(np.sum(np.power(self._std_devs, 2)) / num_thesis)
        # assuming same amount of samples per thesis
        qSwip = np.sqrt(swit*swit/n_samples)

        if self._debug:
            print(f'std dev: {self._std_devs}]')
            print(f'Swit: {swit}]')
            print(f'qSwit: {qSwip}]')
        return qSwip

    def calculateQvalue(self, meansDif, qSwit):
        # See page 93
        return meansDif / qSwit

    def SNK(self):
        # Calculate the standard error of the means
        # See https://www.statisticshowto.com/newman-keuls/

        # Perform pairwise comparisons from large mean to smaller.
        # Sort means by value
        sortMeans, num_thesis = self.sortMeans()

        # Create a letters list to indicate differences
        sigLetters = self._sig_letters.copy()
        self._letterFromI = {}

        # Variance averaning the variance within groups]
        n_samples = np.sum(self._n_samples)
        df = n_samples
        qSwit = self.calculateSwitQ(num_thesis, n_samples)

        # Loop comparing largest with smallest
        # if not difference is found, then skip it
        for k in range(0, num_thesis):
            i = sortMeans[k]
            if len(self._sig_diff[i]):
                continue
            self.SNKcompareTreatments(
                i, k, num_thesis, sortMeans, qSwit, sigLetters, df)

        for index in range(num_thesis):
            thesisNum = self._indexThesis[index]
            self._result[thesisNum]['group'] = self._sig_diff[index]
        if self._debug:
            print(self._result)

    def SNKcompareTreatments(self, i, k, num_thesis, sortMeans, qSwit,
                             sigLetters, df):
        found = False
        for m in range(num_thesis-1, k, -1):
            j = sortMeans[m]
            p = m - k + 1  # Distance between compared groups
            if self._debug:
                print(f'comparing [{i+1}]{self._means[i]}'
                      f' with [{j+1}]{self._means[j]}')
            diff = np.abs(self._means[i] - self._means[j])
            qvalue = self.calculateQvalue(diff, qSwit)
            criticalQ = SNK_Table.qCriticalSNK(df, p)
            if self._debug:
                print(f'comparing q:{qvalue} q_critical:{criticalQ}')
            if qvalue < criticalQ:
                for r in range(m, k, -1):
                    if i not in self._letterFromI:
                        found = True
                        currentLetter = sigLetters.pop(0)
                        self._letterFromI[i] = currentLetter
                        if currentLetter not in self._sig_diff[i]:
                            self._sig_diff[i].append(currentLetter)
                    s = sortMeans[r]
                    if not self._sig_diff[s]:
                        self._sig_diff[s].append(currentLetter)
                        break
        if not found and len(self._sig_diff[i]) == 0:
            self._sig_diff[i].append(sigLetters.pop(0))
        # Not Significantly different. Stop for m loop
        # apply this letters to the rest of the vector
        return found

    def barlett(self):
        self._bartlett_stat, self._bartlett_p = bartlett(*self._data_groups)
        # Print the test statistic and p-value
        text = "<table class='table stats-table'><tr><td>"\
               "<p class='txt-regular-16'>Bartlett statistic</p>"\
               "</td><td></td></tr>"
        text += f"<tr><td>X^2</td><td>{round(self._bartlett_stat,2)}</td><tr>"\
                f"<tr><td>p-value</td><td>{round(self._bartlett_p,3)}</td><tr>"
        self._statsText += text
        if self._debug:
            print(text)

    def levene(self):
        self._levene_stat, self._levene_p = levene(*self._data_groups)
        text = "<table class='table stats-table'><tr><td>"\
               "<p class='txt-regular-16'>Levene statistic</p>"\
               "</td><td></td></tr>"
        text += f"<tr><td>X^2</td><td>{round(self._levene_stat,2)}</td><tr>"\
                f"<tr><td>p-value</td><td>{round(self._levene_p,3)}</td><tr>"
        text += "</table>"
        self._statsText += text
        if self._debug:
            print(text)


class Abbott():
    _data = {}
    _standardNumber = None

    @classmethod
    def do(cls, value, standard):
        if standard != 0:
            return round((value - standard) * 100 / standard, 2)
        else:
            return 0

    def __init__(self, standardNumber, values):
        # values is a dictionary of number of thesis and their values
        # standardIndex in the position of the performance
        # of the standard treatment, or no treatment
        self._standardNumber = standardNumber
        self._data = values

    def run(self):
        efficacies = {}
        if self._standardNumber in self._data:
            efficacyStandard = self._data[self._standardNumber]
        else:
            return None
        if efficacyStandard is None or efficacyStandard == 0:
            return None

        for number in self._data:
            if number != self._standardNumber:
                efficacies[number] = Abbott.do(self._data[number],
                                               efficacyStandard)
        return efficacies
