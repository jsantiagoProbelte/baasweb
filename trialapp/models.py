# Create your models here.
from django.db import models


class ModelHelpers:
    NULL_STRING = '------'
    # Each class should add a list of class:label
    foreignModelLabels = {}

    @classmethod
    def getObjects(cls):
        return cls.objects.all().order_by('name')

    @classmethod
    def returnFormatedItem(self, asDict, id, name):
        if asDict:
            return {'name': name, 'value': id}
        else:
            return (id, name)

    @classmethod
    def getSelectList(cls, addNull=False, asDict=False):
        theList = []
        for item in cls.getObjects():
            theList.append(cls.returnFormatedItem(asDict, item.id, item.name))

        if addNull:
            theList.insert(
                0,
                cls.returnFormatedItem(
                    asDict,
                    None,
                    ModelHelpers.NULL_STRING))

        return theList

    @classmethod
    def initValues(cls, values):
        for value in values:
            cls.objects.create(name=value)

    @classmethod
    def getForeignModels(cls):
        return ModelHelpers.foreignModelLabels

    @classmethod
    def getForeignModelsLabels(cls):
        return list(ModelHelpers.foreignModelLabels.values())

    # @classmethod
    # def addForeignModelLabelPair(cls, foreignClass, label):
    #     ModelHelpers.foreignModelLabels[foreignClass] = label

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

    def __str__(self):
        return self.name


class Crop(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class Plague(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
    scientific = models.CharField(max_length=200, null=True)


class Project(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class Objective(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class Vendor(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class Phase(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class Product(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
    # vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)


class RateUnit(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class ResultUnit(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class TrialStatus(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)


class FieldTrial(models.Model, ModelHelpers):
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

    farmer = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    latitude_str = models.CharField(max_length=100, null=True)
    altitude = models.IntegerField(null=True)

    report_filename = models.TextField(null=True)

    ModelHelpers.foreignModelLabels = {
        Phase: 'phase', Objective: 'objective', Product: 'product',
        Crop: 'crop', Plague: 'plague', Project: 'project'
        }


class Treatment(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    description = models.TextField(null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=5, decimal_places=3)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)


class Application(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
    application_date = models.DateField()
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    crop_stage_majority = models.IntegerField()
    crop_stage_scale = models.CharField(max_length=10)


class Replica(models.Model, ModelHelpers):
    name = models.CharField(max_length=100)
    number = models.IntegerField()
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE)


# This collects the information of other products related with this tests.
class RelatedProducts(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE,
                                  null=True)


"""
Results aggregation
* (RawResult) Value at plant
* (ReplicaResult) Value at Replica (as aggregation of plant' values)
* (AplicationResult) Value at Application connected with a Treatment
    (as aggregation of replica' values)
* (ApplicationMeasurement) An application/treatment could have multiple
    measurements. This one connets to the application / treatment together
    with the unit
"""


class ApplicationMeasurement(models.Model, ModelHelpers):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE)
    unit = models.ForeignKey(ResultUnit, on_delete=models.CASCADE)


class ApplicationResult(models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    result_set = models.ForeignKey(ApplicationMeasurement,
                                   on_delete=models.CASCADE)


class ReplicaResult(models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    application_set = models.ForeignKey(ApplicationMeasurement,
                                        on_delete=models.CASCADE)
    replica = models.ForeignKey(Replica,
                                on_delete=models.CASCADE)


class RawResult(models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    unit = models.ForeignKey(ResultUnit, on_delete=models.CASCADE)
    application_set = models.ForeignKey(ApplicationMeasurement,
                                        on_delete=models.CASCADE)


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
                      'Nemapron', 'Nutrihealth', 'Verticibel'],
            Plague: ['Antracnosis', 'Botrytis', 'Oidio', 'Sphaerotheca',
                     'Cenicilla polvorienta', 'Damping off', 'Gusano soldado',
                     'Marchitez', 'Minador', 'Mosca blanca', 'N/A',
                     'Nematodo agallador', 'Tizon de la hoja',
                     'Tristeza de los citricos', 'Tristeza del aguacatero',
                     'Verticiliosis']
        }

    @classmethod
    def loadInitialTrialValues(cls):
        initialValues = cls.initialTrialModelValues()
        for modelo in initialValues:
            modelo.initValues(initialValues[modelo])
