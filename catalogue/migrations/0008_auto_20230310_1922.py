# Generated by Django 3.2.18 on 2023-03-10 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0007_auto_20230219_0126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batch',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='serial_number',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
