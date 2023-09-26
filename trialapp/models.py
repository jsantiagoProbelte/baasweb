# Create your models here.
from django.db import models
import datetime as dt
from dateutil import relativedelta
from baaswebapp.models import ModelHelpers
from catalogue.models import Product, Treatment, RateUnit
from baaswebapp.models import RateTypeUnit
from django.utils.translation import gettext_lazy as _


class Crop(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    scientific = models.CharField(max_length=100)
    other = models.CharField(max_length=100, null=True)


class CropVariety(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)


class Plague(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    other = models.CharField(max_length=100, null=True)
    scientific = models.CharField(max_length=200, null=True)

    def getName(self):
        if self.scientific:
            return self.scientific
        else:
            return self.name


class Product_Plague(ModelHelpers, models.Model):
    plague = models.ForeignKey(Plague, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Selectors:
        @staticmethod
        def getPlagueProductByProduct(productId):
            return Product_Plague.objects.all().filter(product_id=productId)

        @staticmethod
        def getPlagueNamesByProduct(productId):
            plague_product_list = Product_Plague.Selectors.getPlagueProductByProduct(productId)
            plagues = list(map(lambda product_plague: product_plague.plague.scientific, plague_product_list))

            return plagues

        @staticmethod
        def getPlaguesByProduct(productId):
            plague_product_list = Product_Plague.Selectors.getPlagueProductByProduct(productId)
            plagues = list(map(lambda product_plague: product_plague.plague, plague_product_list))
            print(len(plagues))
            return plagues

        @staticmethod
        def getPlagueProductByPlagues(plagues):
            return Product_Plague.objects.all().filter(plague_id__in=plagues)

    class Meta:
        unique_together = ('product', 'plague')


class Irrigation(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Objective(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class TrialType(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ApplicationMode(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class CultivationMethod(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class PartRated(models.TextChoices):
    FIELD_TRIAL = 'FT', _('Field Trial')
    LAB_TRIAL = 'LT', _('Lab Trial')
    BUNCH = 'BUNCH', _('BUNCH')
    CLUSTR = 'CLUSTR', _('CLUSTR')
    FLOWER = 'FLOWER', _('FLOWER')
    FRUDAM = 'FRUDAM', _('FRUDAM')
    FRUIT = 'FRUIT', _('FRUIT')
    FRUIT_C = 'FRUIT C', _('FRUIT C')
    FRUIT_P = 'FRUIT P', _('FRUIT P')
    FRUROT_C = 'FRUROT C', _('FRUROT C')
    FRUSTO_P = 'FRUSTO P', _('FRUSTO P')
    LEAF = 'LEAF', _('LEAF')
    PLANT = 'PLANT', _('PLANT')
    PLOT = 'PLOT', _('PLOT')
    ROOT = 'ROOT', _('ROOT')
    SPOT = 'SPOT', _('SPOT')
    STEMP = 'STEMP', _('STEMP')
    UNDF = 'UNDF', _('UNDF')


class SoilType(models.TextChoices):
    UNDF = 'UNDF', _('UNDF')
    SANDY = 'Sandy', _('Sandy Soil')  # 'Suelo Arenoso'
    CLAY = 'Clay', _('Clay Soil')  # 'Suelo Arcilloso'
    LOAMY = 'Loamy', _('Loamy Soil')  # 'Suelo Limoso'
    ORGANIC = 'Organic', _('Organic Soil')  # 'Suelo Orgánico'
    ROCKY = 'Rocky', _('Rocky Soil')  # 'Suelo Pedregoso'
    SALINE = 'Saline', _('Saline Soil')  # 'Suelo Salino'
    ALKALINE = 'Alkaline', _('Alkaline Soil')  # 'Suelo Alcalino'
    ACIDIC = 'Acidic', _('Acidic Soil')  # 'Suelo Ácido'
    PEAT = 'Peat', _('Peat Soil')  # 'Suelo de Turba'
    LATERITIC = 'Lateritic', _('Lateritic Soil')  # 'Suelo Laterítico'


class StatusTrial(models.TextChoices):
    PROTOCOL = 'PROT', _('Design Protocol')
    APROVAL = 'APRV', _('Approving Protocol')
    INPROGRESS = 'INPR', _('In Progress')
    REWIEW = 'REVW', _('Review Results')
    DONE = 'DONE', _('Done')


class FieldTrial(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)

    class TrialMeta(models.TextChoices):
        FIELD_TRIAL = 'FT', _('Field Trial')
        LAB_TRIAL = 'LT', _('Lab Trial')
    trial_meta = models.CharField(
        max_length=2,
        choices=TrialMeta.choices,
        default=TrialMeta.FIELD_TRIAL)

    trial_type = models.ForeignKey(TrialType,
                                   on_delete=models.CASCADE, null=True)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    responsible = models.CharField(max_length=100)
    description = models.TextField(null=True)
    conclusion = models.TextField(null=True)

    ref_to_eppo = models.CharField(max_length=100, null=True)
    ref_to_criteria = models.CharField(max_length=100, null=True)
    comments_criteria = models.TextField(null=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    crop_variety = models.ForeignKey(CropVariety,
                                     on_delete=models.CASCADE, null=True)
    plague = models.ForeignKey(Plague, on_delete=models.CASCADE, null=True)

    initiation_date = models.DateField(null=True)
    completion_date = models.DateField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    status_trial = models.CharField(
        max_length=4,
        choices=StatusTrial.choices,
        default=StatusTrial.PROTOCOL)

    contact = models.CharField(max_length=100, null=True)
    cro = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    latitude = models.CharField(max_length=20, null=True)
    longitude = models.CharField(max_length=20, null=True)
    altitude = models.IntegerField(null=True)
    irrigation = models.ForeignKey(Irrigation,
                                   on_delete=models.CASCADE, null=True)
    cultivation = models.ForeignKey(CultivationMethod,
                                    on_delete=models.CASCADE, null=True)
    crop_age = models.IntegerField(null=True)
    seed_date = models.DateField(null=True)
    transplant_date = models.DateField(null=True)
    soil = models.CharField(
        max_length=10,
        choices=SoilType.choices,
        default=SoilType.UNDF)

    blocks = models.IntegerField()
    replicas_per_thesis = models.IntegerField()
    samples_per_replica = models.IntegerField(default=0, null=True)
    distance_between_plants = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    distance_between_rows = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    number_rows = models.IntegerField(default=0, null=True)
    lenght_row = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    net_surface = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    gross_surface = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)

    report_filename = models.TextField(null=True)
    code = models.CharField(max_length=10, null=True)

    application_volume = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    application_volume_unit = models.ForeignKey(
        RateUnit, on_delete=models.CASCADE, null=True)
    mode = models.ForeignKey(ApplicationMode,
                             on_delete=models.CASCADE, null=True)

    public = models.BooleanField(default=False)
    favorable = models.BooleanField(default=False)
    # key properties of the trial after evaluation
    key_thesis = models.IntegerField(null=True)
    control_thesis = models.IntegerField(null=True)
    key_ratetypeunit = models.ForeignKey(RateTypeUnit,
                                         on_delete=models.SET_NULL, null=True)
    key_assessment = models.IntegerField(null=True)
    key_ratedpart = models.CharField(
        max_length=10,
        choices=PartRated.choices,
        default=PartRated.UNDF)
    best_efficacy = models.DecimalField(max_digits=10, decimal_places=2,
                                        null=True)

    avg_temperature = models.IntegerField(null=True)
    avg_humidity = models.IntegerField(null=True)
    avg_precipitation = models.IntegerField(null=True)

    def keyThesis(self):
        if self.key_thesis:
            return Thesis.objects.get(id=self.key_thesis)
        else:
            return None

    @classmethod
    def formatCode(cls, year, month, counts):
        return '{}{}{}'.format(year,
                               str(month).zfill(2),
                               str(counts).zfill(2))

    @classmethod
    def formatLabCode(cls, theDate, counts):
        return '{}{}{}{}'.format(theDate.year,
                                 str(theDate.month).zfill(2),
                                 str(theDate.day).zfill(2),
                                 str(counts).zfill(2))

    @classmethod
    def getCode(cls, theDate, increment):
        year = theDate.year
        month = theDate.month
        start = dt.datetime(year, month, 1)
        end = start + relativedelta.relativedelta(months=+1)
        counts = FieldTrial.objects.filter(
            created__gte=start).filter(
            created__lte=end).count()
        if increment:
            # The object maybe already created or is new
            counts += 1
        return FieldTrial.formatCode(year, month, counts)

    @classmethod
    def getLabCode(cls, theDate, increment):
        counts = FieldTrial.objects.filter(created=theDate).count()
        if increment:
            # The object maybe already created or is new
            counts += 1
        return FieldTrial.formatLabCode(theDate, counts)

    def setCode(self, increment):
        self.code = self.getCode(self.created, increment)
        self.save()

    def setLabCode(self, increment):
        self.code = self.getLabCode(self.created, increment)
        self.save()

    def getDescription(self):
        description = f'{self.crop}'
        if self.plague:
            if not ModelHelpers.isInUnknowns(self.plague.name):
                description += f' + {self.plague}'
        return description

    @classmethod
    def buildTitle(cls, code, crop, plague, location):
        title = f'{code} - {crop}'
        if plague and not ModelHelpers.isInUnknowns(plague):
            title += f' + {plague}'
        if location:
            title += f' . {location}'
        return title

    def getCultivation(self):
        cultivation = self.cultivation.name if self.cultivation else '-'
        cultivation += '<br>'
        cultivation += self.irrigation.name if self.irrigation else '-'
        cultivation += '<br>'
        cultivation += self.soil if self.soil != SoilType.UNDF.value \
            else '-'
        return cultivation

    def getBestEfficacy(self):
        if self.best_efficacy:
            return f'{self.best_efficacy}%'
        else:
            return '??'

    def getLocation(self, showNothing=False):
        if self.location:
            return self.location
        else:
            if showNothing:
                return ''
            else:
                return _('Undefined Location')

    def getPeriod(self):
        period = _('Undefined period')
        if self.initiation_date:
            period = self.initiation_date.strftime("%B")
            if not self.completion_date:
                period += f' {self.initiation_date.year} - ...'
        if self.completion_date:
            if self.completion_date.year == self.initiation_date.year:
                if self.completion_date.month != self.initiation_date.month:
                    period += f' - {self.completion_date.strftime("%B")}'
            else:
                period += f' {self.initiation_date.year}'
                period += f' - {self.completion_date.strftime("%B")}'
            period += f' {self.completion_date.year}'
        return period

    @classmethod
    def createTrial(cls, **kwargs):
        trial = cls.objects.create(
            name=kwargs['name'],
            trial_type=TrialType.objects.get(pk=kwargs['trial_type']),
            status_trial=kwargs['status_trial'],
            objective=Objective.objects.get(pk=kwargs['objective']),
            responsible=kwargs['responsible'],
            product=Product.objects.get(pk=kwargs['product']),
            crop=Crop.objects.get(pk=kwargs['crop']),
            plague=Plague.objects.get(pk=kwargs['plague']),
            initiation_date=kwargs['initiation_date'],
            report_filename=kwargs['report_filename'],
            contact=kwargs['contact'],
            location=kwargs['location'],
            replicas_per_thesis=kwargs['replicas_per_thesis'],
            blocks=kwargs['blocks'],
            latitude=kwargs['latitude'] if 'latitude' in kwargs else None,
            longitude=kwargs['longitude'] if 'longitude' in kwargs else None)
        if 'code' in kwargs:
            trial.code = kwargs['code']
            trial.save()
        else:
            trial.setCode(increment=False)
        return trial

    def plantDensity(self):
        if self.distance_between_plants is not None and\
           self.distance_between_rows is not None:
            numberOfPlants = self.distance_between_plants * \
                self.distance_between_rows
            return round(10000 / numberOfPlants, 2)
        else:
            return None

    def getName(self):
        return self.name

    def get_absolute_url(self):
        if self.trial_meta == FieldTrial.TrialMeta.LAB_TRIAL:
            return "/labtrial/%i/" % self.id
        else:
            return "/fieldtrial_api/%i/" % self.id


class Thesis(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    description = models.TextField(null=True)
    number_applications = models.IntegerField(null=True)
    interval = models.IntegerField(null=True)
    first_application = models.DateField(null=True)
    mode = models.ForeignKey(ApplicationMode,
                             on_delete=models.CASCADE, null=True)
    # This is shadow treatment to allow to be edited in ThesisCreate
    # but actually is stored in TreatmentThesis
    treatment = models.ForeignKey(Treatment,
                                  on_delete=models.CASCADE, null=True)

    @classmethod
    def getObjects(cls, field_trial, as_dict=False):
        objects = cls.objects \
            .filter(field_trial=field_trial) \
            .order_by('number')
        if as_dict:
            return {item.id: item for item in objects}
        else:
            return objects

    @classmethod
    def createThesis(cls, **kwargs):
        fieldTrial = FieldTrial.objects.get(pk=kwargs['field_trial_id'])

        thesis = cls.objects.create(
            name=kwargs['name'],
            field_trial=fieldTrial,
            number=cls.computeNumber(fieldTrial, True),
            description=kwargs['description'],
            number_applications=kwargs['number_applications'],
            interval=kwargs['interval'],
            first_application=kwargs['first_application'])
        if 'mode' in kwargs:
            thesis.mode = kwargs['mode']
            thesis.save()
        return thesis

    @classmethod
    def computeNumber(cls, fieldTrial, increment):
        counts = Thesis.objects.filter(
            field_trial=fieldTrial).count()
        if increment:
            # The object maybe already created or is new
            counts += 1
        return counts

    def getTitle(self):
        return 'T{}: {}'.format(self.number, self.name)

    def get_absolute_url(self):
        return "/thesis_api/%i/" % self.id

    @classmethod
    def getObjectsDisplay(cls, fieldTrial, asArray=False):
        allThesis = Thesis.getObjects(fieldTrial)
        thesisDisplay = []
        if asArray:
            thesisDisplay.append(['#', 'Name', 'Descriptions', 'Treatments'])

        for item in allThesis:
            treatments = ''
            for treatment in TreatmentThesis.getObjects(item):
                if treatments != '':
                    treatments += ' + '
                treatments += treatment.treatment.getName()
            if asArray:
                thesisDisplay.append([
                    item.number, item.name, item.description, treatments])
            else:
                thesisDisplay.append({
                    'name': item.name,
                    'id': item.id,
                    'number': item.number,
                    'description': item.description,
                    'treatments': treatments
                })
        return allThesis, thesisDisplay

    def getKeyProduct(self):
        ttreatements = TreatmentThesis.objects.filter(thesis=self)

        for ttreatement in ttreatements:
            product = ttreatement.treatment.batch.product_variant.product
            if product.vendor and product.vendor.key_vendor:
                return product.name
        return None


class Application(ModelHelpers, models.Model):
    app_date = models.DateField()
    daa = models.IntegerField(null=True)
    daf = models.IntegerField(null=True)
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    comment = models.TextField(null=True)
    bbch = models.CharField(max_length=25)

    @classmethod
    def getObjects(cls, field_trial):
        return cls.objects \
            .filter(field_trial=field_trial) \
            .order_by('app_date')

    @classmethod
    def getObjectsDisplay(cls, field_trial):
        data = [['Date', 'DAA', 'DAF', 'BBCH', 'Comments']]
        for item in cls.getObjects(field_trial):
            data.append([item.app_date, item.daa, item.daf,
                         item.bbch, item.comment])
        return data

    def daysBetween(self, fromDate):
        return (self.app_date-fromDate).days

    @classmethod
    def computeDDT(cls, trial):
        previous = None
        firstApp = None
        # We assume getObjects ordered by date
        for application in cls.getObjects(trial):
            if firstApp is None:
                firstApp = application
            if previous is None:
                application.daa = 0
                application.daf = 0
            else:
                application.daa = application.daysBetween(previous.app_date)
                application.daf = application.daysBetween(firstApp.app_date)
            application.save()
            previous = application

    def getName(self):
        return 'DAF-{}'.format(self.daf)

    def get_absolute_url(self):
        return "/application_api/%i/" % self.id

    def get_success_url(self):
        return "/applicationlist/%i/" % self.field_trial.id


class TreatmentThesis(ModelHelpers, models.Model):
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE)

    @classmethod
    def getObjects(cls, thesis: Thesis):
        return cls.objects \
            .filter(thesis=thesis) \
            .order_by('treatment__name')

    def getName(self):
        return self.treatment.getName()

    @classmethod
    def getTreatment(cls, thesis):
        if thesis:
            tt = cls.objects.filter(thesis=thesis)
            if tt:
                return tt[0].treatment
        return None

    def getDosis(self):
        return self.treatment.getDosis()


class Replica(ModelHelpers, models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=10, null=True)
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)

    @classmethod
    def getObjects(cls, thesis: Thesis):
        return cls.objects \
            .filter(thesis=thesis) \
            .order_by('number')

    def getName(self):
        if self.name:
            return self.name
        else:
            return ('[{}-{}] {}-({},{})').format(
                self.thesis.number,
                self.thesis.name,
                self.number,
                self.pos_x,
                self.pos_y)

    def getKey(self):
        if self.name:
            return self.name
        else:
            return self.number

    def getTitle(self):
        return "T{} - R{}".format(
            self.thesis.number, self.getKey())

    def generateReplicaDataSetId(self, assessment):
        assessmentId = assessment.id if assessment else 'null'
        return 'replica-data-set-{}-{}'.format(
            assessmentId, self.id)

    # create the replicas asociated with this
    @classmethod
    def createReplicas(cls, thesis, replicas_per_thesis):
        replicas = []
        for number in range(0, replicas_per_thesis):
            nameId = 100*(number+1) + thesis.number
            item = Replica.objects.create(
                number=number+1,
                thesis=thesis,
                name=f"{nameId}",
                pos_x=0,
                pos_y=0)
            replicas.append(item.id)
        return replicas

    @classmethod
    def getFieldTrialObjects(cls, field_trial):
        return Replica.objects.filter(
            thesis__field_trial_id=field_trial.id
        ).order_by('thesis__number', 'number')

    @classmethod
    def getDict(cls, trial):
        rict = {}
        for replica in cls.getFieldTrialObjects(trial):
            thesisId = replica.thesis.id
            if thesisId not in rict:
                rict[thesisId] = []
            rict[thesisId].append(replica.id)
        return rict


class Sample(ModelHelpers, models.Model):
    number = models.IntegerField()
    replica = models.ForeignKey(Replica, on_delete=models.CASCADE)

    @classmethod
    def getObjects(cls, replica: Replica):
        return cls.objects \
            .filter(replica=replica) \
            .order_by('number')

    def getName(self):
        return ('[{}-{}] {}-({})').format(
            self.replica.thesis.number,
            self.replica.thesis.name,
            self.replica.number,
            self.number)

    @classmethod
    def createSamples(cls, replica, samples_per_replica):
        for number in range(0, samples_per_replica):
            Sample.objects.create(
                number=number+1,
                replica=replica)

    @classmethod
    def replicaSampleDict(cls, trial):
        # we want a dictionary with sampleId -> replicaId
        theDict = {}
        samples = cls.objects.values(
            'number', 'id', 'replica_id'
            ).filter(replica__thesis__field_trial=trial)
        for sample in samples:
            replicaId = sample['replica_id']
            if replicaId not in theDict:
                theDict[replicaId] = {}
            theDict[replicaId][sample['number']] = sample['id']
        return theDict
