# Create your models here.
from django.db import models
import datetime as dt
from dateutil import relativedelta
from baaswebapp.models import ModelHelpers
from catalogue.models import Product, Treatment
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


class Irrigation(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Project(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Objective(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class TrialType(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ApplicationMode(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class CultivationMethod(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class TrialStatus(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


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

    ref_to_eppo = models.CharField(max_length=100, null=True)
    ref_to_criteria = models.CharField(max_length=100, null=True)
    comments_criteria = models.TextField(null=True)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    crop_variety = models.ForeignKey(CropVariety,
                                     on_delete=models.CASCADE, null=True)
    plague = models.ForeignKey(Plague, on_delete=models.CASCADE, null=True)

    initiation_date = models.DateField(null=True)
    completion_date = models.DateField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    trial_status = models.ForeignKey(TrialStatus,
                                     on_delete=models.CASCADE, null=True)

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
    mode = models.ForeignKey(ApplicationMode,
                             on_delete=models.CASCADE, null=True)

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

    @classmethod
    def create_fieldTrial(cls, **kwargs):
        trial = cls.objects.create(
            name=kwargs['name'],
            trial_type=TrialType.objects.get(pk=kwargs['trial_type']),
            trial_status=TrialStatus.objects.get(pk=kwargs['trial_status']),
            objective=Objective.objects.get(pk=kwargs['objective']),
            responsible=kwargs['responsible'],
            product=Product.objects.get(pk=kwargs['product']),
            project=Project.objects.get(pk=kwargs['project']),
            crop=Crop.objects.get(pk=kwargs['crop']),
            plague=Plague.objects.get(pk=kwargs['plague']),
            initiation_date=kwargs['initiation_date'],
            report_filename=kwargs['report_filename'],
            contact=kwargs['contact'],
            location=kwargs['location'],
            replicas_per_thesis=kwargs['replicas_per_thesis'],
            blocks=kwargs['blocks'])
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
    def getObjects(cls, field_trial):
        return cls.objects \
                .filter(field_trial=field_trial) \
                .order_by('number')

    @classmethod
    def create_Thesis(cls, **kwargs):
        fieldTrial = FieldTrial.objects.get(pk=kwargs['field_trial_id'])

        thesis = cls.objects.create(
            name=kwargs['name'],
            field_trial=fieldTrial,
            number=cls.computeNumber(fieldTrial, True),
            description=kwargs['description'],
            number_applications=kwargs['number_applications'],
            interval=kwargs['interval'],
            first_application=kwargs['first_application']
            )
        if 'mode' in kwargs:
            thesis.mode = kwargs['mode']
            thesis.save()
        return thesis

    def getReferenceIndexDataInput(self):
        return self.number

    def getBackgroundColor(self):
        return self.number

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

    @classmethod
    def getObjectsPerFieldTrial(cls, fieldTrial: FieldTrial):
        return cls.objects \
                .filter(thesis__field_trial=fieldTrial) \
                .order_by('treatment__name')

    @classmethod
    def getSelectListFieldTrial(cls, fieldTrial: FieldTrial,
                                addNull=False, asDict=False):
        return cls._getSelectList(
            cls.getObjectsPerFieldTrial(fieldTrial),
            asDict=asDict,
            addNull=addNull)

    @classmethod
    def create_TreatmentThesis(cls, **kwargs):
        return cls.objects.create(
            thesis=Thesis.objects.get(pk=kwargs['thesis_id']),
            product=Treatment.objects.get(pk=kwargs['treatment_id']))

    def getName(self):
        return self.treatment.getName()

    def __str__(self):
        return self.getName()


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

    def getShortName(self):
        return self.getKey()

    def getTitle(self):
        return "Thesis {} - Replica {}".format(
            self.thesis.name, self.getKey())

    def generateReplicaDataSetId(self, assessment):
        assessmentId = assessment.id if assessment else 'null'
        return 'replica-data-set-{}-{}'.format(
            assessmentId, self.id)

    # create the replicas asociated with this
    @classmethod
    def createReplicas(cls, thesis, replicas_per_thesis):
        for number in range(0, replicas_per_thesis):
            Replica.objects.create(
                number=number+1,
                thesis=thesis,
                pos_x=0,
                pos_y=0)

    @classmethod
    def getFieldTrialObjects(cls, field_trial):
        ids = Thesis.objects.filter(
            field_trial=field_trial
            ).order_by('number').values_list('id', flat=True)

        return Replica.objects.filter(
            thesis_id__in=ids
            ).order_by('thesis__number', 'number')

    def getReferenceIndexDataInput(self):
        return self.thesis.getName()

    def getBackgroundColor(self):
        return self.thesis.getBackgroundColor()


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

    def getKey(self):
        return self.number

    def getShortName(self):
        return ('{}-[{}]-{}').format(
            self.replica.thesis.name,
            self.replica.number,
            self.number)

    def getReferenceIndexDataInput(self):
        return self.replica.getName()

    def getBackgroundColor(self):
        return self.replica.getBackgroundColor()

    @classmethod
    def createSamples(cls, replica, samples_per_replica):
        for number in range(0, samples_per_replica):
            Sample.objects.create(
                number=number+1,
                replica=replica)
