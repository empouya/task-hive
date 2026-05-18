from django.db import migrations


def backfill_project_soft_delete_flags(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(deleted_at__isnull=False).update(is_deleted=True)


def reverse_backfill_project_soft_delete_flags(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(is_deleted=True).update(is_deleted=False)


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_project_deleted_at_project_deleted_by_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_project_soft_delete_flags,
            reverse_backfill_project_soft_delete_flags,
        ),
    ]