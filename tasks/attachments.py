from django.shortcuts import get_object_or_404

from common.exceptions import PermissionDeniedError
from common.permissions import can_read_team, can_write_tasks
from tasks.models import Task, TaskAttachment


def create_task_attachment(*, user, task_id, file):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)
    team = task.project.team

    if not can_write_tasks(user, team):
        raise PermissionDeniedError("You do not have permission to attach files to this task.")

    return TaskAttachment.objects.create(
        team=team,
        task=task,
        uploaded_by=user,
        file=file,
        original_filename=file.name,
        content_type=getattr(file, "content_type", ""),
        size=file.size,
    )


def list_task_attachments(*, user, task_id):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if not can_read_team(user, task.project.team):
        raise PermissionDeniedError("You do not have access to this task.")

    return task.attachments.select_related("uploaded_by").order_by("-created_at")


def delete_task_attachment(*, user, attachment_id):
    attachment = get_object_or_404(
        TaskAttachment.objects.select_related("task__project__team"),
        id=attachment_id,
    )

    if not can_write_tasks(user, attachment.task.project.team):
        raise PermissionDeniedError("You do not have permission to delete this attachment.")

    attachment.soft_delete(deleted_by=user)
    return attachment