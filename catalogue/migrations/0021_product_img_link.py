# Generated by Django 4.2.4 on 2023-09-18 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0020_product_mixes'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='img_link',
            field=models.URLField(max_length=300, null=True),
        ),
    ]