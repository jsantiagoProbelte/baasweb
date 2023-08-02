from django.db import models
from baaswebapp.models import ModelHelpers
from trialapp.models import FieldTrial
from catalogue.models import RateUnit, Batch
from baaswebapp.models import RateTypeUnit
from trialapp.data_models import DataModel


class LabAssessment(ModelHelpers, models.Model):
    assessment_date = models.DateField()
    trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    rate_type = models.ForeignKey(RateTypeUnit, on_delete=models.CASCADE)

    def getPartRated(self):
        return ''


class LabDosis(ModelHelpers, models.Model):
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    rate_unit = models.ForeignKey(RateUnit, on_delete=models.CASCADE)

    @classmethod
    def createLabDosis(cls):
        created = []
        rateUnit = RateUnit.findOrCreate(name='mg/ml')
        for dosis in [0, 0.25, 0.74, 2.22, 6.66, 20]:
            created.append(
                LabDosis.findOrCreate(rate=dosis, rate_unit=rateUnit))
        return created


class LabThesis(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True)
    trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)

    @classmethod
    def createLabThesis(cls, trial):
        LabThesis.objects.create(name='DIPEL', trial=trial)
        for i in range(0, trial.replicas_per_thesis - 1):
            LabThesis.objects.create(name='Thesis {}'.format(i),
                                     trial=trial)
        return LabThesis.objects.filter(trial=trial).order_by('name')

    @classmethod
    def getObjectsByTrial(cls, trial):
        return LabThesis.objects.filter(trial=trial).order_by('name')


class LabDataPoint(DataModel, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    total = models.DecimalField(max_digits=5, decimal_places=3, null=True)
    dosis = models.ForeignKey(LabDosis, on_delete=models.CASCADE)
    thesis = models.ForeignKey(LabThesis, on_delete=models.CASCADE)
    assessment = models.ForeignKey(LabAssessment, on_delete=models.CASCADE)
