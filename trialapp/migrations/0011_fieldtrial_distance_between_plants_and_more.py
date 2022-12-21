# Generated by Django 4.1.2 on 2022-12-10 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0010_applicationmode_thesis_first_application_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='distance_between_plants',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='distance_between_rows',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='gross_surface',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='lenght_row',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='net_surface',
            field=models.DecimalField(decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='number_rows',
            field=models.IntegerField(default=0, null=True),
        ),
    ]