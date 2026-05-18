from django.db import migrations


def backfill_task_soft_delete_flags(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    Task.objects.filter(deleted_at__isnull=False).update(is_deleted=True)


def reverse_backfill_task_soft_delete_flags(apps, schema_editor):
    Task = apps.get_model("tasks", "Task")
    Task.objects.filter(is_deleted=True).update(is_deleted=False)


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0002_task_deleted_at_task_deleted_by_task_is_deleted_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_task_soft_delete_flags,
            reverse_backfill_task_soft_delete_flags,
        ),
    ]
