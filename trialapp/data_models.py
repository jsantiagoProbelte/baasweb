from django.db import models
from django.db.models import Avg
from django.forms import model_to_dict
from baaswebapp.models import ModelHelpers, RateTypeUnit
from trialapp.models import FieldTrial, Thesis, Sample, Replica, PartRated


class Assessment(ModelHelpers, models.Model):
    name = models.CharField(max_length=100)
    assessment_date = models.DateField()
    part_rated = models.CharField(
        max_length=10,
        choices=PartRated.choices,
        default=PartRated.UNDF)
    field_trial = models.ForeignKey(FieldTrial, on_delete=models.CASCADE)
    crop_stage_majority = models.CharField(max_length=25)
    rate_type = models.ForeignKey(RateTypeUnit, on_delete=models.CASCADE)
    daf = models.IntegerField(null=True)

    @classmethod
    def getObjects(cls, field_trial, date_order=True):
        if date_order:
            first_order = 'assessment_date'
            second_order = 'rate_type__name'
            third_order = 'rate_type__unit'
            forth_order = 'part_rated'
        else:
            forth_order = 'assessment_date'
            first_order = 'rate_type__name'
            second_order = 'rate_type__unit'
            third_order = 'part_rated'
        return cls.objects.filter(
            field_trial=field_trial).order_by(
            first_order, second_order, third_order, forth_order)

    def getName(self):
        return "{}-BBCH".format(
            self.crop_stage_majority)

    def getContext(self):
        if self.crop_stage_majority is None or\
           self.crop_stage_majority == ModelHelpers.UNDEFINED:
            return self.rate_type.getName()
        else:
            return "{}-BBCH {}".format(
                self.crop_stage_majority,
                self.rate_type.getName())

    def get_absolute_url(self):
        return "/assessment/%i/" % self.id

    def getTitle(self):
        return "[{}] {}".format(self.assessment_date,
                                self.rate_type)

    def getUnitPartTitle(self):
        return "{} {}".format(self.rate_type.getName(),
                              self.getPartRated())

    def get_success_url(self):
        return "/assessment_list/%i/" % self.field_trial.id

    @classmethod
    def getRateSets(cls, assessments):
        rateTypeUnits = {}
        for assessment in assessments:
            if assessment.rate_type.id not in rateTypeUnits:
                rateTypeUnits[assessment.rate_type.id] = assessment.rate_type
        return list(rateTypeUnits.values())

    @classmethod
    def getRatedParts(cls, assessments):
        ratedParts = {}
        for assessment in assessments:
            if assessment.part_rated not in ratedParts:
                ratedParts[assessment.part_rated] = assessment.part_rated
        return list(ratedParts.keys())

    def getPartRated(self):
        if self.part_rated == 'Undefined' or self.part_rated == 'None':
            return ''
        return self.part_rated

    @classmethod
    def computeDDT(cls, trial):
        firstItem = None
        # We assume getObjects ordered by date
        for item in cls.getObjects(trial):
            if firstItem is None:
                firstItem = item
                item.daf = 0
            else:
                item.daf = (item.assessment_date -
                            firstItem.assessment_date).days
            item.save()

    def create(self, fieldTrial, **attributes):
        assessment = Assessment.objects.create(
                        name=attributes['name'],
                        assessment_date=attributes['assessment_date'],
                        part_rated=attributes['part_rated'],
                        field_trial=FieldTrial.objects.get(pk=fieldTrial.id) if fieldTrial else None,
                        crop_stage_majority=attributes['crop_stage_majority'],
                        rate_type=RateTypeUnit.objects.get(pk=attributes['rate_type']) if 'rate_type' else None,
                        daf=attributes['daf']
                    )

        return assessment

    def clone(self, fieldtrial):
        assessment = self.create(fieldtrial, **model_to_dict(self))

        assessment.save()
        return assessment

    @classmethod
    def cloneAll(cls, oldFieldTrial, newFieldTrial):
        assessmentList = cls.objects.all().filter(field_trial=oldFieldTrial.id)
        cloned_list = list()

        for assessment in assessmentList:
            cloned_list.append(assessment.clone(newFieldTrial))

        return cloned_list


class DataModel(ModelHelpers):
    @classmethod
    def generateDataPointId(cls, level, assessment,
                            reference, fakeId=0):
        return 'data-point-{}-{}-{}-{}'.format(
            level, assessment.id, reference.id, fakeId)

    @classmethod
    def genDataPointId(cls, level, assessmentId,
                       referenceId, fakeId=0):
        return 'data-point-{}-{}-{}-{}'.format(
            level, assessmentId, referenceId, fakeId)

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
        return cls.objects.filter(assessment=assessment)


class ThesisData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)
    reference = models.ForeignKey(Thesis,
                                  on_delete=models.CASCADE)

    @classmethod
    def dataPointsAssess(cls, assIds):
        return cls.objects.values(
            'id', 'reference__id', 'value', 'assessment__id',
            'reference__number'
            ).filter(assessment_id__in=assIds).order_by(
            'reference__number')


class ReplicaData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.ForeignKey(Replica,
                                  on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)

    @classmethod
    def dataPointsAssess(cls, assIds):
        return cls.objects.values(
                'reference__thesis__id', 'reference__name', 'value',
                'reference__id', 'assessment__id',
                'reference__thesis__number'
            ).filter(
                assessment_id__in=assIds
            ).order_by(
                'reference__thesis__number', 'reference__number')

    @classmethod
    def dataPointsAssessAvg(cls, assIds):
        return cls.objects.values(
                'reference__thesis__id', 'assessment__id',
                'reference__thesis__number'
            ).annotate(
                value=Avg('value')
            ).filter(
                assessment_id__in=assIds
            ).order_by(
                'reference__thesis__number', 'assessment__assessment_date')

    @classmethod
    def dataPointsKeyAssessAvg(cls, keyRateTypeUnit, keyPartRated,
                               keyThesis, untreatedThesis):
        return cls.objects.values(
                'reference__thesis__id', 'assessment__id',
                'reference__thesis__number', 'assessment__name',
                "reference__thesis__name"
            ).annotate(
                value=Avg('value')
            ).filter(
                reference__thesis__id__in=[untreatedThesis, keyThesis],
                assessment__part_rated=keyPartRated,
                assessment__rate_type=keyRateTypeUnit
            ).order_by(
                'reference__thesis__number', 'assessment__assessment_date')


class SampleData(DataModel, models.Model):
    value = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.ForeignKey(Sample,
                                  on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment,
                                   on_delete=models.CASCADE)

    @classmethod
    def getDataPointsPerSampleNumber(cls, assessment, number):
        return cls.objects.filter(
                assessment=assessment,
                reference__number=number).\
            order_by('reference__number')

    @classmethod
    def dataPointsAssess(cls, assIds):
        return cls.objects.values(
            'reference__replica__id', 'value',
            'reference__id', 'assessment__id',
            'reference__replica__thesis__id',
            'reference__replica__thesis__number',
            'reference__replica__number'
            ).filter(assessment_id__in=assIds).order_by(
            'reference__replica__number', 'reference__number')
