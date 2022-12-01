# Create your models here.
from django.db import models


class ModelHelpers:
    NULL_STRING = '------'

    @classmethod
    def getObjects(cls):
        return cls.objects.all().order_by('name')

    @classmethod
    def returnFormatedItem(cls, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        return cls._getSelectList(cls.getObjects(),
                                  addNull=addNull,
                                  asDict=asDict)

    @classmethod
    def _getSelectList(cls, items, addNull=False, asDict=False):
        theList = []
        for item in items:
            theList.append(cls.returnFormatedItem(
                asDict, item.id, item.getName()))

        if addNull:
            theList.insert(
                0,
                cls.returnFormatedItem(
                    asDict,
                    None,
                    ModelHelpers.NULL_STRING))

        return theList

    @classmethod
    def initKValues(cls, kValues, location='default'):
        for item in kValues:
            theObject = cls(**item)
            theObject.save(using=location)

    @classmethod
    def getForeignModels(cls):
        if hasattr(cls, 'foreignModelLabels'):
            return cls.foreignModelLabels
        else:
            return {}

    @classmethod
    def getForeignModelsLabels(cls):
        if hasattr(cls, 'foreignModelLabels'):
            return list(cls.foreignModelLabels.values())
        else:
            return []

    @classmethod
    def generateFormKwargsChoices(cls, initialValues):
        dictModelLabel = cls.getForeignModels()
        dictKwargsChoices = {dictModelLabel[model]: model.getSelectList()
                             for model in dictModelLabel}
        dictKwargsChoices['initial'] = initialValues
        return dictKwargsChoices

    @classmethod
    def extractValueModelChoicesFromKwargs(cls, kwargs):
        modelValues = {}
        for label in cls.getForeignModelsLabels():
            modelValues[label] = cls.extractTagsFromKwargs(kwargs, label)
        return modelValues

    @classmethod
    def extractTagsFromKwargs(cls, kwargs, label):
        values = None
        if label in kwargs:
            values = kwargs[label]
            kwargs.pop(label, None)
        else:
            pass  # TODO: Assert !!
        return values

    @classmethod
    def getValueFromRequestOrArray(cls, request, values, label):
        if label in values:
            return values[label]
        else:
            if label in request.POST:
                return request.POST[label]
            else:
                return None

    def getKey(self):
        return self.getName()

    def getName(self):
        return self.name

    def __str__(self):
        return self.getName()

    @classmethod
    def generateDataPointId(cls, level, evaluation,
                            reference, unit):
        return 'data-point-{}-{}-{}-{}'.format(
            level, evaluation.id,
            reference.id, unit.id)

    @classmethod
    def setDataPoint(cls, reference, evaluation, unit, value):
        dataPoint = cls.objects.filter(
            evaluation=evaluation,
            reference=reference,
            unit=unit).all()
        if not dataPoint:
            cls.objects.create(
                evaluation=evaluation,
                reference=reference,
                unit=unit,
                value=value)
        else:
            dataPoint[0].value = value
            dataPoint[0].save()

    @classmethod
    def getDataPoints(cls, evaluation):
        return cls.objects \
                  .filter(evaluation=evaluation)


class Crop(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    scientific = models.CharField(max_length=100)


class CropVariety(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)


class Plague(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    scientific = models.CharField(max_length=200, null=True)


class Project(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Objective(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Vendor(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Phase(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)


class Product(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    # vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)


class RateUnit(ModelHelpers, models.Model):
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
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, null=True)
    objective = models.ForeignKey(Objective, on_delete=models.CASCADE)
    responsible = models.CharField(max_length=100)

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    plague = models.ForeignKey(Plague, on_delete=models.CASCADE)

    initiation_date = models.DateField(null=True)
    completion_date = models.DateField(null=True)
    # trial_status = models.ForeignKey(TrialStatus, on_delete=models.CASCADE)

    contact = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    altitude = models.IntegerField(null=True)

    report_filename = models.TextField(null=True)

    blocks = models.IntegerField()
    replicas_per_thesis = models.IntegerField()
    samples_per_replica = models.IntegerField(default=0, null=True)

    foreignModelLabels = {
        Phase: 'phase', Objective: 'objective', Product: 'product',
        Crop: 'crop', Plague: 'plague', Project: 'project'
        }

    @classmethod
    def create_fieldTrial(cls, **kwargs):
        return cls.objects.create(
            name=kwargs['name'],
            phase=Phase.objects.get(pk=kwargs['phase']),
            objective=Objective.objects.get(pk=kwargs['objective']),
            responsible=kwargs['responsible'],
            product=Product.objects.get(pk=kwargs['product']),
            project=Project.objects.get(pk=kwargs['project']),
            crop=Crop.objects.get(pk=kwargs['crop']),
            plague=Plague.objects.get(pk=kwargs['plague']),
            initiation_date=kwargs['initiation_date'],
            contact=kwargs['contact'],
            location=kwargs['location'],
            replicas_per_thesis=kwargs['replicas_per_thesis'],
            blocks=kwargs['blocks']
        )


class Thesis(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    description = models.TextField(null=True)

    @classmethod
    def getObjects(cls, field_trial):
        return cls.objects \
                .filter(field_trial=field_trial) \
                .order_by('number')

    @classmethod
    def create_Thesis(cls, **kwargs):
        return cls.objects.create(
            name=kwargs['name'],
            field_trial=FieldTrial.objects.get(pk=kwargs['field_trial_id']),
            number=kwargs['number'],
            description=kwargs['description'])

    def getReferenceIndexDataInput(self):
        return self.number

    def getBackgroundColor(self):
        return self.number


class ProductThesis(ModelHelpers, models.Model):
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=5, decimal_places=3)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)

    foreignModelLabels = {
        Product: 'product', RateUnit: 'rate_unit'
        }

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
            rate_unit=RateUnit.objects.get(pk=kwargs['rate_unit_id'])
        )

    def getName(self):
        return ('[{}-{}] <{}, {} {}>').format(
            self.thesis.number,
            self.thesis.name,
            self.product.name,
            self.rate,
            self.rate_unit.name)


class Replica(ModelHelpers, models.Model):
    number = models.IntegerField()
    thesis = models.ForeignKey(Thesis, on_delete=models.CASCADE)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)

    @classmethod
    def getObjects(cls, thesis: Thesis):
        return cls.objects \
                .filter(thesis=thesis) \
                .order_by('number')

    def getName(self):
        return ('[{}-{}] {}-({},{})').format(
            self.thesis.number,
            self.thesis.name,
            self.number,
            self.pos_x,
            self.pos_y)

    def getKey(self):
        return self.number

    def getShortName(self):
        return self.number

    def getTitle(self):
        return "Thesis {} - Replica {}".format(
            self.thesis.name, self.number)

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
    crop_stage_majority = models.IntegerField()
    crop_stage_scale = models.CharField(max_length=10)

    @classmethod
    def getObjects(cls, field_trial):
        return cls.objects \
                .filter(field_trial=field_trial) \
                .order_by('evaluation_date')

    def getName(self):
        return "{}-{}".format(
            self.crop_stage_majority,
            self.crop_stage_scale)


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


class ThesisData(ModelHelpers, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Thesis,
                                  on_delete=models.CASCADE)


class ReplicaData(ModelHelpers, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Replica,
                                  on_delete=models.CASCADE)


class SampleData(ModelHelpers, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Sample,
                                  on_delete=models.CASCADE)

    @classmethod
    def getDataPoints(cls, evaluation, replica):
        items = []
        for sample in Sample.getObjects(replica):
            dataPoints = SampleData.objects.filter(
                    evaluation=evaluation,
                    reference=sample).\
                order_by('reference__number')
            for dataPoint in dataPoints:
                items.append(dataPoint)
        return items


class TrialStats:
    @classmethod
    def getGeneralStats(cls):
        return {
            'products': Product.objects.count(),
            'field_trials': FieldTrial.objects.count(),
            'points': ThesisData.objects.count()
        }


'''
To create db execute this in python manage.py shell
from trialapp.models import TrialDbInitialLoader
TrialDbInitialLoader.loadInitialTrialValues()
'''


class TrialDbInitialLoader:
    @classmethod
    def initialTrialModelValues(cls):
        return {
            Crop: ['Agave', 'Avocado', 'Strawberry', 'Melon', 'Watermelon',
                   'Tomato', 'Potato', 'Cotton', 'Blackberry', 'Corn',
                   'Brocoli', 'Citrics', 'Onion', 'Raspberry', 'Banan',
                   'Jitomate', 'Chili', 'Pumkin', 'Cucumber', 'Carrot'],
            Phase: ['Positioning', 'Development', 'Registry'],
            Project: ['Botrybel', 'ExBio', 'Belnatol', 'Belthirul', 'Biopron',
                      'Biopron', 'Bulhnova', 'Canelys', 'ChemBio', 'Mimotem',
                      'Nemapron', 'Nutrihealth', 'Verticibel'],
            Objective: ['Reduce fertilizer', 'Efectividad Biologica'],
            Product: ['Botrybel', 'ExBio', 'Belnatol', 'Belthirul', 'Biopron',
                      'Biopron', 'Bulhnova', 'Canelys', 'ChemBio', 'Mimotem',
                      'Nemapron', 'Nutrihealth', 'Verticibel',
                      '-- No Product --'],
            Plague: ['Antracnosis', 'Botrytis', 'Oidio', 'Sphaerotheca',
                     'Cenicilla polvorienta', 'Damping off', 'Gusano soldado',
                     'Marchitez', 'Minador', 'Mosca blanca', 'N/A',
                     'Nematodo agallador', 'Tizon de la hoja',
                     'Tristeza de los citricos', 'Tristeza del aguacatero',
                     'Verticiliosis'],
            RateUnit: ['Kg/hectare', 'Liters/hectare'],
            AssessmentUnit: ['%; 0; 100', '%UNCK; -; -'],
            AssessmentType: ['PHYGEN', 'PESSEV', 'PESINC', 'CONTRO']
        }

    @classmethod
    def loadInitialTrialValues(cls, location='default'):
        initialValues = cls.initialTrialModelValues()
        for modelo in initialValues:
            kValues = [{'name': value} for value in initialValues[modelo]]
            modelo.initKValues(kValues, location=location)
