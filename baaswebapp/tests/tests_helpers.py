from django.test import Client
from django.contrib import auth
from baaswebapp.models import Weather
from baaswebapp.data_loaders import TrialDbInitialLoader
from trialapp.models import FieldTrial, Thesis, Replica, StatusTrial
from trialapp.data_models import ReplicaData, Assessment, ThesisData
from rest_framework.test import APIRequestFactory


# Create your tests here.
class TrialTestData:
    TRIALS = [{
            'name': 'fieldTrial 666',
            'trial_type': 1,
            'status_trial': StatusTrial.PROTOCOL,
            'objective': 1,
            'responsible': 'Waldo',
            'product': 1,
            'crop': 1,
            'plague': 1,
            'initiation_date': '2021-07-01',
            'contact': 'Mr Farmer',
            'location': 'La Finca',
            'report_filename': '',
            'repetitions': 4,
            'latitude': 38.2796,
            'longitude': -0.7914,
            'type': 1,
            'status': 1}
    ]

    THESIS = [{
        'number': 1,
        'name': 'thesis 666',
        'description': 'Thesis 666 for product 1',
        'field_trial_id': 1,
        'number_applications': 5,
        'interval': 14,
        'first_application': '2021-01-01',
        # 'mode': 1 Use mode and not mode_id in post calls
        }, {
        'name': 'thesis 777',
        'description': 'Thesis 777 for product 2',
        'field_trial_id': 1,
        'number_applications': 5,
        'interval': 7,
        'first_application': '2021-01-01',
        'mode_id': 2
        }
    ]

    PRODUCT_THESIS = [{
        'thesis_id': 1,
        'product_id': 1,
        'rate': 1.5,
        'rate_unit_id': 1},
        {
        'thesis_id': 1,
        'product_id': 2,
        'rate': 5,
        'rate_unit_id': 1},
        {
        'thesis_id': 2,
        'product_id': 1,
        'rate': 3,
        'rate_unit_id': 1}
    ]

    ASSESSMENT = [{
        'field_trial_id': 1,
        'name': 'Primera aplication',
        'assessment_date': '2022-07-01',
        'crop_stage_majority': 66,
        'rate_type': 2,
    }]

    APPLICATION = [{
        'field_trial_id': 1,
        'comment': 'Primera aplication',
        'app_date': '2022-07-01',
        'bbch': 66
        },
        {
        'field_trial_id': 1,
        'comment': 'segunda aplication',
        'app_date': '2022-07-17',
        'bbch': 67},
        {
        'field_trial_id': 1,
        'comment': 'segunda aplication',
        'app_date': '2022-07-10',
        'bbch': 67
    }]

    @staticmethod
    def addWeatherData(ass):
        Weather.objects.create(
            date=ass.assessment_date,
            recent=False,
            latitude=float(ass.field_trial.latitude),
            longitude=float(ass.field_trial.longitude),
            max_temp=30.0,
            min_temp=15.0,
            mean_temp=20.0,
            soil_temp_0_to_7cm=10.0,
            soil_temp_7_to_28cm=10.0,
            soil_temp_28_to_100cm=10.0,
            soil_temp_100_to_255cm=10.0,
            soil_moist_0_to_7cm=10.0,
            soil_moist_7_to_28cm=10.0,
            soil_moist_28_to_100cm=10.0,
            soil_moist_100_to_255cm=10.0,
            dew_point=10.0,
            relative_humidity=10.0,
            precipitation=10.0,
            precipitation_hours=10.0,
            max_wind_speed=10.0)


class DataGenerator:
    _fieldTrials = {}
    _assessments = {}
    SAMPLES = 6
    dataAssessment = {
        '15 DA-E': {
            1: [97.60, 97.20, 97.20],
            2: [98.40, 97.20, 97.60],
            3: [97.60, 97.60, 97.20],
            4: [98.80, 98.40, 98.80],
            5: [85.20, 85.20, 88.00],
            6: [97.20, 96.00, 96.40],
            7: [97.60, 97.60, 96.80],
            8: [97.60, 97.60, 98.80],
            9: [93.20, 88.80, 92.80],
            10: [31.20, 21.20, 18.80]},
        'PageTest': {
            1: [164, 172, 177, 156, 195],
            2: [178, 191, 182, 185, 177],
            3: [175, 193, 171, 163, 176],
            4: [155, 166, 164, 170, 168]},
        '12 DA-D': {
            1: [54.5, 38.9, 17.5, 28.6],
            2: [54.5, 69.4, 62.5, 100],
            3: [0, 81.7, 18.2, 60.7],
            4: [75.2, 8.3, 47.5, 0],
            5: [0, 0, 0, 0]}}

    def __init__(self, replicaGen=True, thesisGen=False,
                 sampleGen=False, num_samples=SAMPLES):
        TrialDbInitialLoader.loadInitialTrialValues()
        # Create as many as trials as assessments to try
        # different conditions
        assessList = list(self.dataAssessment.keys())
        num_assessments = len(assessList)
        for i in range(num_assessments):
            theses = {}
            replicas = {}
            trialData = TrialTestData.TRIALS[0].copy()
            trialData['name'] = f"trial{i}"
            trial = FieldTrial.createTrial(**trialData)
            self._fieldTrials[i] = trial

            if sampleGen:
                # We do not need to create samples
                # They are created when data is inputed
                # But we need to modify the fieldTrial
                trial.samples_per_replica = num_samples
                trial.save()

            assName = assessList[i]
            assInfo = {
                'name': assName,
                'assessment_date': '2022-05-14',
                'rate_type_id': 1,
                'part_rated': 'LEAF, P',
                'crop_stage_majority': '89, 89, 89',
                'field_trial_id': trial.id}
            self._assessments[assName] = Assessment.objects.create(**assInfo)
            assId = self._assessments[assName].id
            assData = self.dataAssessment[assName]
            num_thesis = len(assData.keys())
            num_replicas = len(assData[1])
            for j in range(1, num_thesis+1):
                thesis = Thesis.objects.create(
                    name='{}'.format(j),
                    number=j,
                    field_trial_id=trial.id)
                theses[j] = thesis
                replicas[j] = Replica.createReplicas(thesis, num_replicas)

                if replicaGen:
                    for index in range(num_replicas):
                        ReplicaData.objects.create(
                            assessment_id=assId,
                            reference_id=replicas[j][index],
                            value=assData[j][index])

                if thesisGen:
                    ThesisData.objects.create(
                        assessment_id=assId,
                        reference_id=thesis.id,
                        value=assData[j][0])


class UserStub:
    username = None
    is_superuser = None
    is_staff = None

    def __init__(self, name, superUser, is_staff):
        self.username = name
        self.is_superuser = superUser
        self.is_staff = is_staff


class ApiRequestHelperTest(APIRequestFactory):

    PASSWORD = 'BaaSisAwesome'
    USER = 'Waldo'
    _user = None

    def __init__(self, is_admin=False):
        super().__init__()
        self.createUser(is_admin=is_admin)

    def login(self):
        client = Client.login(
            username=ApiRequestHelperTest.USER,
            password=ApiRequestHelperTest.PASSWORD)
        return auth.get_user(client)

    def createUser(self, is_admin=False):
        User = auth.get_user_model()
        self._user = User.objects.create_user(
            ApiRequestHelperTest.USER, 'temporary@gmail.com',
            ApiRequestHelperTest.PASSWORD)
        if is_admin:
            self._user.is_superuser = True
            self._user.save()

    def setUser(self, request):
        request.user = self._user
