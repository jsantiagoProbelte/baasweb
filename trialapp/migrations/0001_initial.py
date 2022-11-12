# Generated by Django 4.1.2 on 2022-11-11 13:28

from django.db import migrations, models
import django.db.models.deletion
import trialapp.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssessmentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='AssessmentUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Crop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('scientific', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('evaluation_date', models.DateField()),
                ('crop_stage_majority', models.IntegerField()),
                ('crop_stage_scale', models.CharField(max_length=10)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='FieldTrial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('responsible', models.CharField(max_length=100)),
                ('initiation_date', models.DateField(null=True)),
                ('completion_date', models.DateField(null=True)),
                ('farmer', models.CharField(max_length=100, null=True)),
                ('location', models.CharField(max_length=100, null=True)),
                ('latitude_str', models.CharField(max_length=100, null=True)),
                ('altitude', models.IntegerField(null=True)),
                ('report_filename', models.TextField(null=True)),
                ('rows_layout', models.IntegerField()),
                ('replicas_per_thesis', models.IntegerField()),
                ('samples_per_replica', models.IntegerField(default=0)),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.crop')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Phase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Plague',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('scientific', models.CharField(max_length=200, null=True)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='RateUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Thesis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('number', models.IntegerField()),
                ('description', models.TextField(null=True)),
                ('field_trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='TrialStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='TrialAssessmentSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.assessmenttype')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.assessmentunit')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='ThesisData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=3, max_digits=5)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation')),
                ('reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.thesis')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='SampleData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=3, max_digits=5)),
                ('reference', models.IntegerField()),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='ReplicaData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=3, max_digits=5)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation')),
                ('reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.thesis')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='Replica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.thesis')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='ProductThesis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=3, max_digits=5)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.product')),
                ('rate_unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.rateunit')),
                ('thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.thesis')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.CreateModel(
            name='ProductEvaluation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation')),
                ('product_thesis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.productthesis')),
                ('thesis', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.thesis')),
            ],
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='objective',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.objective'),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='phase',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.phase'),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='plague',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.plague'),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.product'),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.project'),
        ),
        migrations.AddField(
            model_name='evaluation',
            name='field_trial',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.fieldtrial'),
        ),
        migrations.CreateModel(
            name='CropVariety',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('crop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trialapp.crop')),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
    ]
