# Generated by Django 3.2.18 on 2023-04-09 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0036_auto_20230326_0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='daf',
            field=models.IntegerField(null=True),
        ),
    ]
