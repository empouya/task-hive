from django.db import migrations


def backfill_comment_soft_delete_flags(apps, schema_editor):
    Comment = apps.get_model("comments", "Comment")
    Comment.objects.filter(deleted_at__isnull=False).update(is_deleted=True)


def reverse_backfill_comment_soft_delete_flags(apps, schema_editor):
    Comment = apps.get_model("comments", "Comment")
    Comment.objects.filter(is_deleted=True).update(is_deleted=False)


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0002_comment_deleted_at_comment_deleted_by_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_comment_soft_delete_flags,
            reverse_backfill_comment_soft_delete_flags,
        ),
    ]
