# Generated by Django 4.2.1 on 2023-09-28 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0052_merge_20230928_1120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='part_rated',
            field=models.CharField(choices=[('BUNCH', 'bunch'), ('CLUSTR', 'CLUSTR'), ('FLOWER', 'FLOWER'), ('FRUDAM', 'FRUDAM'), ('FRUIT', 'FRUIT'), ('FRUIT C', 'FRUIT C'), ('FRUIT P', 'FRUIT P'), ('FRUROT C', 'FRUROT C'), ('FRUSTO P', 'FRUSTO P'), ('LEAF', 'LEAF'), ('PLANT', 'PLANT'), ('PLOT', 'PLOT'), ('ROOT', 'ROOT'), ('SPOT', 'SPOT'), ('STEMP', 'STEMP'), ('UNDF', 'UNDF')], default='UNDF', max_length=10),
        ),
        migrations.AlterField(
            model_name='fieldtrial',
            name='key_ratedpart',
            field=models.CharField(choices=[('BUNCH', 'bunch'), ('CLUSTR', 'CLUSTR'), ('FLOWER', 'FLOWER'), ('FRUDAM', 'FRUDAM'), ('FRUIT', 'FRUIT'), ('FRUIT C', 'FRUIT C'), ('FRUIT P', 'FRUIT P'), ('FRUROT C', 'FRUROT C'), ('FRUSTO P', 'FRUSTO P'), ('LEAF', 'LEAF'), ('PLANT', 'PLANT'), ('PLOT', 'PLOT'), ('ROOT', 'ROOT'), ('SPOT', 'SPOT'), ('STEMP', 'STEMP'), ('UNDF', 'UNDF')], default='UNDF', max_length=10),
        ),
    ]
