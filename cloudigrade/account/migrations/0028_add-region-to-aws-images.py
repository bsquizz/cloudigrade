# Generated by Django 2.1.2 on 2019-01-17 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0027_update_machineimage_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='awsmachineimage',
            name='region',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]