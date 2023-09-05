# Generated by Django 4.2.1 on 2023-09-05 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0042_fieldtrial_best_efficacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='key_assessment',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='soil',
            field=models.CharField(choices=[('UNDF', 'UNDF'), ('Sandy', 'Sandy Soil'), ('Clay', 'Clay Soil'), ('Loamy', 'Loamy Soil'), ('Organic', 'Organic Soil'), ('Rocky', 'Rocky Soil'), ('Saline', 'Saline Soil'), ('Alkaline', 'Alkaline Soil'), ('Acidic', 'Acidic Soil'), ('Peat', 'Peat Soil'), ('Lateritic', 'Lateritic Soil')], default='UNDF', max_length=10),
        ),
    ]
