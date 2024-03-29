# Generated by Django 4.2.1 on 2023-08-24 15:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('baaswebapp', '0002_weather'),
        ('trialapp', '0040_remove_fieldtrial_project_delete_project'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='key_ratedpart',
            field=models.CharField(choices=[('FT', 'Field Trial'), ('LT', 'Lab Trial'), ('BUNCH', 'BUNCH'), ('CLUSTR', 'CLUSTR'), ('FLOWER', 'FLOWER'), ('FRUDAM', 'FRUDAM'), ('FRUIT', 'FRUIT'), ('FRUIT C', 'FRUIT C'), ('FRUIT P', 'FRUIT P'), ('FRUROT C', 'FRUROT C'), ('FRUSTO P', 'FRUSTO P'), ('LEAF', 'LEAF'), ('PLANT', 'PLANT'), ('PLOT', 'PLOT'), ('ROOT', 'ROOT'), ('SPOT', 'SPOT'), ('STEMP', 'STEMP'), ('UNDF', 'UNDF')], default='UNDF', max_length=10),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='key_ratetypeunit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='baaswebapp.ratetypeunit'),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='key_thesis',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='untreated_thesis',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='assessment',
            name='part_rated',
            field=models.CharField(choices=[('FT', 'Field Trial'), ('LT', 'Lab Trial'), ('BUNCH', 'BUNCH'), ('CLUSTR', 'CLUSTR'), ('FLOWER', 'FLOWER'), ('FRUDAM', 'FRUDAM'), ('FRUIT', 'FRUIT'), ('FRUIT C', 'FRUIT C'), ('FRUIT P', 'FRUIT P'), ('FRUROT C', 'FRUROT C'), ('FRUSTO P', 'FRUSTO P'), ('LEAF', 'LEAF'), ('PLANT', 'PLANT'), ('PLOT', 'PLOT'), ('ROOT', 'ROOT'), ('SPOT', 'SPOT'), ('STEMP', 'STEMP'), ('UNDF', 'UNDF')], default='UNDF', max_length=10),
        ),
    ]
