# Generated by Django 3.2.18 on 2023-02-28 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0027_application_daf'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fieldtrial',
            name='latitude_str',
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='latitude',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='longitude',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
