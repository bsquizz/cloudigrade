# Generated by Django 3.2.10 on 2021-12-20 20:43

from django.db import migrations


def delete_deprecated_tasks(apps, schema_editor):
    """Delete recently deprecated task objects."""
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    deprecated_tasks = [
        "api.clouds.aws.tasks.ensure_all_verify_tasks_are_valid",
        "api.clouds.aws.tasks.scale_up_inspection_cluster",
        "api.clouds.aws.tasks.verify_account_permissions",
    ]
    PeriodicTask.objects.filter(task__in=deprecated_tasks).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0053_remove_awscloudaccount_verify_task"),
    ]

    operations = [migrations.RunPython(delete_deprecated_tasks)]