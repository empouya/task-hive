from django.db import migrations


def backfill_team_soft_delete_flags(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Team.objects.filter(deleted_at__isnull=False).update(is_deleted=True)


def reverse_backfill_team_soft_delete_flags(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Team.objects.filter(is_deleted=True).update(is_deleted=False)


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0004_team_deleted_by_team_is_deleted_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_team_soft_delete_flags,
            reverse_backfill_team_soft_delete_flags,
        ),
    ]
