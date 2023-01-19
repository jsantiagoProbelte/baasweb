from django.db import models
from baaswebapp.models import ModelHelpers
from trialapp.models import Evaluation, TrialAssessmentSet, FieldTrial,\
                            Thesis, Sample, Replica


class DataHelper(ModelHelpers):
    @classmethod
    def getDataPointsFieldTrial(cls, fieldTrial):
        evaluationIds = [item.id for item in Evaluation.getObjects(fieldTrial)]
        return cls.objects \
                  .filter(evaluation_id__in=evaluationIds)

    @classmethod
    def getDataPointsProduct(cls, product, crop, plague, assessmentType):
        filterTrials = {'product__id': product.id,
                        'crop__id': crop.id}
        if plague:
            filterTrials['plague__id'] = plague.id

        fieldTrials = FieldTrial.objects.filter(**filterTrials).values('id')
        if len(fieldTrials) == 0:
            return [], []
        fieldTrialIds = [item['id'] for item in fieldTrials]

        trialAssessmentSets = TrialAssessmentSet.objects.filter(
            field_trial_id__in=fieldTrialIds,
            type_id=assessmentType.id).all()
        setIds = [item.id for item in trialAssessmentSets]
        dataSets = cls.objects.filter(unit_id__in=setIds)
        return dataSets, trialAssessmentSets

    @classmethod
    def distinctValues(cls, product, tag):
        tag_id = '{}__id'.format(tag)
        tag_name = '{}__name'.format(tag)
        results = FieldTrial.objects.filter(product=product).values(
            tag_id, tag_name)
        return ModelHelpers.extractDistincValues(results, tag_id, tag_name)

    @classmethod
    def getCrops(cls, product):
        return cls.distinctValues(product, 'crop')

    @classmethod
    def getPlagues(cls, product):
        return cls.distinctValues(product, 'plague')

    @classmethod
    def dimensionsValues(cls, product):
        results = FieldTrial.objects.filter(product=product).values('id')
        ids = [value['id'] for value in results]
        tag = 'type'
        # We need the id from the set, but we display the name from the type
        tag_id = '{}__id'.format(tag)
        tag_name = '{}__name'.format(tag)
        results = TrialAssessmentSet.objects.filter(
            field_trial_id__in=ids).values(tag_id, tag_name)
        return ModelHelpers.extractDistincValues(results, tag_id, tag_name)

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()


class ThesisData(DataHelper, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Thesis,
                                  on_delete=models.CASCADE)


class ReplicaData(DataHelper, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Replica,
                                  on_delete=models.CASCADE)


class SampleData(DataHelper, models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=3)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Sample,
                                  on_delete=models.CASCADE)

    @classmethod
    def getDataPointsReplica(cls, evaluation, replica):
        items = []
        for sample in Sample.getObjects(replica):
            dataPoints = SampleData.objects.filter(
                    evaluation=evaluation,
                    reference=sample).\
                order_by('reference__number')
            for dataPoint in dataPoints:
                items.append(dataPoint)
        return items
