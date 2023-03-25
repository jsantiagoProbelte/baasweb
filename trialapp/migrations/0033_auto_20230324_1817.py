# Generated by Django 3.2.18 on 2023-03-24 17:17

import baaswebapp.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baaswebapp', '__first__'),
        ('trialapp', '0032_delete_rateunit'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('assessment_date', models.DateField()),
                ('part_rated', models.CharField(max_length=100, null=True)),
                ('crop_stage_majority', models.CharField(max_length=25)),
                ('field_trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial')),
                ('rate_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='baaswebapp.ratetypeunit')),
            ],
            bases=(baaswebapp.models.ModelHelpers, models.Model),
        ),
        migrations.AddField(
            model_name='replicadata',
            name='assessment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.assessment'),
        ),
        migrations.AddField(
            model_name='sampledata',
            name='assessment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.assessment'),
        ),
        migrations.AddField(
            model_name='thesisdata',
            name='assessment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.assessment'),
        ),
    ]
