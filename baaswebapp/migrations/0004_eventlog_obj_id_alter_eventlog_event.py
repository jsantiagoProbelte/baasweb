# Generated by Django 4.2.1 on 2023-09-16 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baaswebapp', '0003_eventlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventlog',
            name='obj_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='eventlog',
            name='event',
            field=models.CharField(choices=[('UNK', 'Unknown'), ('N_T', 'new trial'), ('U_T', 'update trial'), ('N_P', 'new product'), ('U_P', 'update product')], default='UNK', max_length=10),
        ),
    ]
