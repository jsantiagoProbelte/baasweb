# Generated by Django 3.2.16 on 2022-12-14 10:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0011_fieldtrial_distance_between_plants_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Phase',
            new_name='TrialType',
        ),
        migrations.RenameField(
            model_name='fieldtrial',
            old_name='phase',
            new_name='trial_type',
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='trial_status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialstatus'),
        ),
    ]
