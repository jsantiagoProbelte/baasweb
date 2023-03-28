# Generated by Django 3.2.18 on 2023-03-25 09:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0033_auto_20230324_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='replicadata',
            name='evaluation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation'),
        ),
        migrations.AlterField(
            model_name='replicadata',
            name='unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset'),
        ),
        migrations.AlterField(
            model_name='sampledata',
            name='evaluation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation'),
        ),
        migrations.AlterField(
            model_name='sampledata',
            name='unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset'),
        ),
        migrations.AlterField(
            model_name='thesisdata',
            name='evaluation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.evaluation'),
        ),
        migrations.AlterField(
            model_name='thesisdata',
            name='unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.trialassessmentset'),
        ),
    ]
