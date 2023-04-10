import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baaswebapp.dev')
django.setup()

from trialapp.models import FieldTrial  # noqa: E402
from trialapp.data_models import Assessment  # noqa: E402


class StatsGenerator:
    def createDates(self):
        for trial in FieldTrial.objects.all():
            print('{}'.format(trial.code))
            Assessment.computeDDT(trial)

    def createStats(self):
        for trial in FieldTrial.objects.all():
            print('{}'.format(trial.code))


if __name__ == '__main__':
    generator = StatsGenerator()
    generator.createDates()
