# Generated by Django 4.2.1 on 2023-09-12 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0047_fieldtrial_status_trial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fieldtrial',
            name='trial_status',
        ),
        migrations.DeleteModel(
            name='TrialStatus',
        ),
    ]