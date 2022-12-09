# Generated by Django 4.1.2 on 2022-12-09 13:28

from django.db import migrations, models
import django.db.models.deletion
import trialapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0009_fieldtrial_code_fieldtrial_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationMode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            bases=(trialapp.models.ModelHelpers, models.Model),
        ),
        migrations.AddField(
            model_name='thesis',
            name='first_application',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='thesis',
            name='interval',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='thesis',
            name='number_applications',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='thesis',
            name='mode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='trialapp.applicationmode'),
        ),
    ]
