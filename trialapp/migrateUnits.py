import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')
django.setup()

from baaswebapp.models import RateTypeUnit   # noqa: E402
from trialapp.models import FieldTrial, TrialAssessmentSet,\
    Evaluation  # noqa: E402
from trialapp.data_models import Assessment, ThesisData, ReplicaData,\
     SampleData  # noqa: E402


def migrateUnits():
    for trial in FieldTrial.objects.all():
        print("> {}".format(trial.code))
        oldSets = TrialAssessmentSet.objects.filter(field_trial=trial)
        typeUnits = {}
        for oldSet in oldSets:
            rateType = RateTypeUnit.findOrCreate(
                name=oldSet.type.name, unit=oldSet.unit.name)
            typeUnits[oldSet.id] = rateType.id

        evaluations = Evaluation.objects.filter(field_trial=trial)
        for evaluation in evaluations:
            print('> > {}'.format(evaluation.name))
            for assSet in oldSets:
                print('> > >{}'.format(assSet.type.name))
                assessment = Assessment.findOrCreate(
                            name=evaluation.name,
                            assessment_date=evaluation.evaluation_date,
                            part_rated='',
                            field_trial_id=evaluation.field_trial.id,
                            crop_stage_majority=evaluation.crop_stage_majority,
                            rate_type_id=typeUnits[assSet.id])
                totalpoints = 0
                for classData in [ThesisData, ReplicaData, SampleData]:
                    dataPoints = classData.getDataPointsAssSet(evaluation,
                                                               assSet)
                    if len(dataPoints) > 0:
                        totalpoints += len(dataPoints)
                        for dataPoint in dataPoints:
                            if dataPoint.assessment is None:
                                dataPoint.assessment = assessment
                                dataPoint.save()
                if totalpoints == 0:
                    print('> > > > deleteing this, no points found')
                    assessment.delete()
                else:
                    print('> > > > {}'.format(totalpoints))


if __name__ == '__main__':
    migrateUnits()
