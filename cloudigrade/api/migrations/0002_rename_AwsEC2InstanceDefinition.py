# Generated by Django 2.1.5 on 2019-05-13 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_v2_models'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AwsEC2InstanceDefinitions',
            new_name='AwsEC2InstanceDefinition',
        ),
    ]
