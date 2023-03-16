from django.db import models
from baaswebapp.models import ModelHelpers
from trialapp.models import Evaluation, TrialAssessmentSet, FieldTrial,\
                            Thesis, Sample, Replica, AssessmentType


class DataModel(ModelHelpers):
    @classmethod
    def generateDataPointId(cls, level, evaluation, unit,
                            reference, fakeId=0):
        return 'data-point-{}-{}-{}-{}-{}'.format(
            level, evaluation.id, unit.id, reference.id, fakeId)

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
            # This should not happen, but in that case, remove items
            for i in range(1, len(dataPoint)):
                dataPoint[i].delete()

    @classmethod
    def getDataPoints(cls, evaluation):
        return cls.objects \
                  .filter(evaluation=evaluation)

    @classmethod
    def getDataPointsAssSet(cls, evaluation, assSet):
        return cls.objects \
                  .filter(evaluation=evaluation,
                          unit=assSet)

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
        theArray, theIds = ModelHelpers.extractDistincValues(results, tag_id,
                                                             tag_name)
        return theArray

    @classmethod
    def getCrops(cls, product):
        return cls.distinctValues(product, 'crop')

    @classmethod
    def getPlagues(cls, product):
        return cls.distinctValues(product, 'plague')

    @classmethod
    def dimensionsValues(cls, product, as_array=True):
        results = FieldTrial.objects.filter(product=product).values('id')
        ids = [value['id'] for value in results]
        tag = 'type'
        # We need the id from the set, but we display the name from the type
        tag_id = '{}__id'.format(tag)
        tag_name = '{}__name'.format(tag)
        results = TrialAssessmentSet.objects.filter(
                field_trial_id__in=ids).values(tag_id, tag_name)
        dimensions, theIds = ModelHelpers.extractDistincValues(results, tag_id,
                                                               tag_name)
        if as_array:
            return dimensions
        else:
            return AssessmentType.objects.filter(id__in=theIds)

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()


class ThesisData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Thesis,
                                  on_delete=models.CASCADE)


class ReplicaData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Replica,
                                  on_delete=models.CASCADE)


class SampleData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    evaluation = models.ForeignKey(Evaluation,
                                   on_delete=models.CASCADE)
    unit = models.ForeignKey(TrialAssessmentSet,
                             on_delete=models.CASCADE)
    reference = models.ForeignKey(Sample,
                                  on_delete=models.CASCADE)

    @classmethod
    def getDataPointsPerSampleNumber(cls, evaluation, assSet, number):
        return SampleData.objects.filter(
                    evaluation=evaluation,
                    unit=assSet,
                    reference__number=number).\
                order_by('reference__number')
