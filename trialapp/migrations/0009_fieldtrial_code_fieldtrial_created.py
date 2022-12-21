# Generated by Django 4.1.2 on 2022-12-09 00:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0008_remove_fieldtrial_filename'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='code',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='fieldtrial',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]