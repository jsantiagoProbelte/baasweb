# Create your models here.
from django.db import models
import datetime as dt
from dateutil import relativedelta
from baaswebapp.models import ModelHelpers
from catalogue.models import Product


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


class Project(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Objective(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class TrialType(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class RateUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class ApplicationMode(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class AssessmentUnit(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)


class AssessmentType(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)


class TrialStatus(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class FieldTrial(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
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
    plague = models.ForeignKey(Plague, on_delete=models.CASCADE)

    initiation_date = models.DateField(null=True)
    completion_date = models.DateField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    trial_status = models.ForeignKey(TrialStatus,
                                     on_delete=models.CASCADE, null=True)

    contact = models.CharField(max_length=100, null=True)
    cro = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    altitude = models.IntegerField(null=True)

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

    foreignModelLabels = {
        TrialType: 'trial_type', Objective: 'objective', Product: 'product',
        Crop: 'crop', Plague: 'plague', Project: 'project',
        TrialStatus: 'trial_status'}

    @classmethod
    def formatCode(cls, year, month, counts):
        return '{}{}{}'.format(year,
                               str(month).zfill(2),
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

    def setCode(self, increment):
        self.code = self.getCode(self.created, increment)
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

    foreignModelLabels = {ApplicationMode: 'mode'}

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
            first_application=kwargs['first_application'])
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


class ProductThesis(ModelHelpers, models.Model):
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)
    foreignModelLabels = {Product: 'product', RateUnit: 'rate_unit'}

    @classmethod
    def getObjects(cls, thesis: Thesis):
        return cls.objects \
                .filter(thesis=thesis) \
                .order_by('product__name')

    @classmethod
    def getObjectsPerFieldTrial(cls, fieldTrial: FieldTrial):
        objects = []
        for thesis in Thesis.getObjects(fieldTrial):
            for productThesis in ProductThesis.getObjects(thesis):
                objects.append(productThesis)
        return objects

    @classmethod
    def getSelectListFieldTrial(cls, fieldTrial: FieldTrial,
                                addNull=False, asDict=False):
        return cls._getSelectList(
            cls.getObjectsPerFieldTrial(fieldTrial),
            asDict=asDict,
            addNull=addNull)

    @classmethod
    def create_ProductThesis(cls, **kwargs):
        return cls.objects.create(
            thesis=Thesis.objects.get(pk=kwargs['thesis_id']),
            product=Product.objects.get(pk=kwargs['product_id']),
            rate=kwargs['rate'],
            rate_unit=RateUnit.objects.get(pk=kwargs['rate_unit_id']))

    def getName(self):
        return ('[{}-{}] <{}, {} {}>').format(
            self.thesis.number,
            self.thesis.name,
            self.product.name,
            self.rate,
            self.rate_unit.name)


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

    def generateReplicaDataSetId(self, evaluation):
        evaluationId = evaluation.id if evaluation else 'null'
        return 'replica-data-set-{}-{}'.format(
            evaluationId, self.id)

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


# This collects which moments in times, do we evaluate the thesis
class Evaluation(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    evaluation_date = models.DateField()
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    crop_stage_majority = models.CharField(max_length=25)

    @classmethod
    def getObjects(cls, field_trial):
        return cls.objects \
                .filter(field_trial=field_trial) \
                .order_by('evaluation_date')

    def getName(self):
        return "{}-BBCH".format(
            self.crop_stage_majority)


# This collects which products are included in each evaluation
class ProductEvaluation(models.Model):
    product_thesis = models.ForeignKey(ProductThesis, on_delete=models.CASCADE)
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE,
                               null=True)
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE)

    @classmethod
    def getObjects(cls, evaluation: Evaluation):
        return cls.objects \
                .filter(evaluation=evaluation) \
                .order_by('thesis__number', 'product_thesis__product__name')

    def getName(self):
        return self.product_thesis.getName()


"""
Results aggregation
* (RawResult) Value at plant
* (ReplicaResult) Value at Replica (as aggregation of plant' values)
* (AplicationResult) Value at Evaluation connected with a Thesis
    (as aggregation of replica' values)
* (EvaluationMeasurement) An evaluation/treatment could have multiple
    measurements. This one connects to the evaluation / treatment together
    with the unit
"""


# This collects which assessment units are used in each fieldtrial
class TrialAssessmentSet(ModelHelpers, models.Model):
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    type = models.ForeignKey(AssessmentType, on_delete=models.CASCADE)
    unit = models.ForeignKey(AssessmentUnit, on_delete=models.CASCADE)

    @classmethod
    def getObjects(cls, fieldTrial):
        return cls.objects \
                  .filter(field_trial=fieldTrial) \
                  .order_by('unit__name')
