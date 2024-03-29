# Generated by Django 4.2.1 on 2023-09-27 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0049_alter_fieldtrial_soil'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtrial',
            name='soil',
            field=models.CharField(choices=[('UNDF', 'UNDF'), ('Sandy', 'Sandy Soil'), ('Clay', 'Clay Soil'), ('Loamy', 'Loamy Soil'), ('ClayLoamy', 'Clay Loamy'), ('Organic', 'Organic Soil'), ('Rocky', 'Rocky Soil'), ('Saline', 'Saline Soil'), ('Alkaline', 'Alkaline Soil'), ('Acidic', 'Acidic Soil'), ('Peat', 'Peat Soil'), ('Lateritic', 'Lateritic Soil')], default='UNDF', max_length=10),
        ),
    ]
