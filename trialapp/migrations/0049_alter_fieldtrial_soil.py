# Generated by Django 4.2.1 on 2023-09-27 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0048_remove_fieldtrial_trial_status_delete_trialstatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtrial',
            name='soil',
            field=models.CharField(choices=[('UNDF', 'UNDF'), ('Sandy', 'Sandy Soil'), ('Clay', 'Clay Soil'), ('Loamy', 'Loamy Soil'), ('ClayLoamy', 'Clay Loam'), ('Organic', 'Organic Soil'), ('Rocky', 'Rocky Soil'), ('Saline', 'Saline Soil'), ('Alkaline', 'Alkaline Soil'), ('Acidic', 'Acidic Soil'), ('Peat', 'Peat Soil'), ('Lateritic', 'Lateritic Soil')], default='UNDF', max_length=10),
        ),
    ]
