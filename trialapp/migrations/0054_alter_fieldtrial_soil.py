# Generated by Django 4.2.1 on 2023-09-28 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0053_alter_assessment_part_rated_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtrial',
            name='soil',
            field=models.CharField(choices=[('UNDF', 'UNDF'), ('Clay', 'Clay Soil'), ('ClayLoamy', 'Clay Loamy'), ('Sandy', 'Sandy Soil'), ('SandyClay', 'Sandy Clay'), ('SandyLoam', 'Sandy Loam'), ('Loamy', 'Loamy Soil'), ('Organic', 'Organic Soil'), ('Rocky', 'Rocky Soil'), ('Saline', 'Saline Soil'), ('Alkaline', 'Alkaline Soil'), ('Acidic', 'Acidic Soil'), ('Peat', 'Peat Soil'), ('Lateritic', 'Lateritic Soil'), ('SiltLoam', 'Silt Loam')], default='UNDF', max_length=10),
        ),
    ]