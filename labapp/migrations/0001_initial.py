# Generated by Django 3.2.18 on 2023-04-26 09:26

import baaswebapp.models
from django.db import migrations, models
import django.db.models.deletion
import trialapp.data_models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('baaswebapp', '0001_initial'),
        ('trialapp', '0038_fieldtrial_trial_meta'),
        ('catalogue', '0008_auto_20230310_1922'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assessment_date', models.DateField()),
                ('rate_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='baaswebapp.ratetypeunit')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial')),
            ],
            bases=(baaswebapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='LabThesis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('batch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='catalogue.batch')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial')),
            ],
            bases=(baaswebapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='LabDosis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('rate_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.rateunit')),
            ],
            bases=(baaswebapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='LabDataPoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=3, max_digits=5)),
                ('total', models.DecimalField(decimal_places=3, max_digits=5, null=True)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labapp.labassessment')),
                ('dosis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labapp.labdosis')),
                ('thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labapp.labthesis')),
            ],
            bases=(trialapp.data_models.DataModel, models.Model),
        ),
    ]