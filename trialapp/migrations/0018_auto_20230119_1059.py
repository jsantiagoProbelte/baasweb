# Generated by Django 3.2.16 on 2023-01-19 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0003_auto_20230119_1038'),
        ('trialapp', '0017_delete_vendor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtrial',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.product'),
        ),
        migrations.AlterField(
            model_name='productthesis',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalogue.product'),
        ),
        migrations.DeleteModel(
            name='Product',
        ),
    ]
