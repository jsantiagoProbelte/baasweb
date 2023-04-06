from django.db import models
from baaswebapp.models import ModelHelpers, RateTypeUnit
from trialapp.models import FieldTrial, Thesis, Sample, Replica


class Assessment(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    assessment_date = models.DateField()
    part_rated = models.CharField(max_length=100, null=True)
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    crop_stage_majority = models.CharField(max_length=25)
    rate_type = models.ForeignKey(RateTypeUnit, on_delete=models.CASCADE)

    @classmethod
    def getObjects(cls, field_trial):
        return cls.objects \
                .filter(field_trial=field_trial) \
                .order_by('assessment_date', 'rate_type', 'part_rated')

    def getName(self):
        return "{}-BBCH".format(
            self.crop_stage_majority)

    def getContext(self):
        return "{}-BBCH {}".format(
            self.crop_stage_majority,
            self.rate_type.getName())

    def get_absolute_url(self):
        return "/assessment_api/%i/" % self.id

    def getTitle(self):
        return "[{}] {}".format(self.assessment_date,
                                self.name)

    @classmethod
    def getRateSets(cls, assessments):
        rateUnits = {}
        for assessment in assessments:
            if assessment.rate_type.id not in rateUnits:
                rateUnits[assessment.rate_type.id] = assessment.rate_type
        return list(rateUnits.values())

    @classmethod
    def getRatedParts(cls, assessments):
        ratedParts = {}
        for assessment in assessments:
            if assessment.part_rated not in ratedParts:
                ratedParts[assessment.part_rated] = assessment.part_rated
        return list(ratedParts.values())


class DataModel(ModelHelpers):
    @classmethod
    def generateDataPointId(cls, level, assessment,
                            reference, fakeId=0):
        return 'data-point-{}-{}-{}-{}'.format(
            level, assessment.id, reference.id, fakeId)

    @classmethod
    def setDataPoint(cls, reference, assessment, value):
        dataPoint = cls.objects.filter(
            assessment=assessment,
            reference=reference).all()
        if not dataPoint:
            cls.objects.create(
                assessment=assessment,
                reference=reference,
                value=value)
        else:
            dataPoint[0].value = value
            dataPoint[0].save()
            # This should not happen, but in that case, remove items
            for i in range(1, len(dataPoint)):
                dataPoint[i].delete()

    @classmethod
    def getDataPoints(cls, assessment):
        return cls.objects \
                  .filter(assessment=assessment)

    @classmethod
    def getDataPointsAssessment(cls, assessment):
        return cls.objects \
                  .filter(assessment=assessment)

    @classmethod
    def getDataPointsFieldTrial(cls, fieldTrial):
        assIds = [item.id for item in Assessment.getObjects(fieldTrial)]
        return cls.getAssessmentDataPoints(assIds)

    @classmethod
    def getAssessmentDataPoints(cls, assIds):
        return cls.objects.filter(assessment_id__in=assIds)

    @classmethod
    def getDataPointsProduct(cls, product, crop, plague, rateType):
        filterTrials = {'product__id': product.id,
                        'crop__id': crop.id}
        if plague:
            filterTrials['plague__id'] = plague.id

        fieldTrials = FieldTrial.objects.filter(**filterTrials).values('id')
        if len(fieldTrials) == 0:
            return [], []
        fieldTrialIds = [item['id'] for item in fieldTrials]

        assessments = Assessment.objects.filter(
            field_trial_id__in=fieldTrialIds,
            rate_type_id=rateType.id).all()
        setIds = [item.id for item in assessments]
        dataSets = cls.objects.filter(assessment_id__in=setIds)
        return dataSets

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
        tag = 'rate_type'
        # We need the id from the set, but we display the name from the type
        tag_id = '{}__id'.format(tag)
        tag_name = '{}__name'.format(tag)
        results = Assessment.objects.filter(
                field_trial_id__in=ids).values(tag_id, tag_name)
        dimensions, theIds = ModelHelpers.extractDistincValues(results, tag_id,
                                                               tag_name)
        if as_array:
            return dimensions
        else:
            return RateTypeUnit.objects.filter(id__in=theIds)

    @classmethod
    def getCountFieldTrials(cls, product):
        return FieldTrial.objects.filter(product=product).count()


class ThesisData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)
    reference = models.ForeignKey(Thesis,
                                  on_delete=models.CASCADE)


class ReplicaData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.ForeignKey(Replica,
                                  on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)


class SampleData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.ForeignKey(Sample,
                                  on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)

    @classmethod
    def getDataPointsPerSampleNumber(cls, assessment, number):
        return SampleData.objects.filter(
                    assessment=assessment,
                    reference__number=number).\
                order_by('reference__number')
