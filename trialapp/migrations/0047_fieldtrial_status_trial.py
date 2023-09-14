# Generated by Django 4.2.1 on 2023-09-12 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trialapp', '0046_fieldtrial_favorable'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtrial',
            name='status_trial',
            field=models.CharField(choices=[('PROT', 'Design Protocol'), ('APRV', 'Approving Protocol'), ('INPR', 'In Progress'), ('REVW', 'Review Results'), ('DONE', 'Done')], default='PROT', max_length=4),
        ),
    ]
