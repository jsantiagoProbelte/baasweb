# Generated by Django 3.2.16 on 2023-01-24 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0019_auto_20230120_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='replica',
            name='name',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
