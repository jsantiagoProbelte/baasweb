# Generated by Django 3.2.18 on 2023-04-11 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0037_assessment_daf'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='trial_meta',
            field=models.CharField(choices=[('FT', 'Field Trial'), ('LT', 'Lab Trial')], default='FT', max_length=2),
        ),
    ]
