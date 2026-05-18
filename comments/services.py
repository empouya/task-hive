from django.shortcuts import get_object_or_404

from common.exceptions import PermissionDeniedError
from common.permissions import can_comment, can_manage_projects, can_read_team
from realtime.events import comment_payload, publish_team_event
from comments.models import Comment
from projects.models import Project
from tasks.models import Task


def create_comment(*, user, task_id, data):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)
    team = task.project.team

    if not can_comment(user, team):
        raise PermissionDeniedError("You do not have permission to comment on this task.")

    if task.project.status == Project.Status.ARCHIVED:
        raise PermissionDeniedError("Project is archived.")

    comment = Comment.objects.create(
        task=task,
        author=user,
        content=data["content"],
    )
    publish_team_event(
        team_id=team.id,
        event_type="comment.created",
        payload=comment_payload(comment),
    )
    return comment


def list_comments(*, user, task_id):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if not can_read_team(user, task.project.team):
        raise PermissionDeniedError("You do not have access to this task.")

    return (
        task.comments
        .select_related("author")
        .order_by("created_at")
    )


def delete_comment(*, user, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related("task__project__team"),
        id=comment_id,
    )

    if not can_manage_projects(user, comment.task.project.team):
        raise PermissionDeniedError("Only team managers and admins can moderate comments.")

    comment.soft_delete(deleted_by=user)
    publish_team_event(
        team_id=comment.task.project.team_id,
        event_type="comment.deleted",
        payload={"comment": {"id": comment.id, "task_id": comment.task_id}},
    )
    return comment