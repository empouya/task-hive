from celery import shared_task

from realtime.events import notification_payload, publish_team_event
from comments.models import Comment
from notifications.models import Notification
from tasks.models import Task


@shared_task
def create_comment_notification(comment_id):
    try:
        comment = Comment.objects.select_related(
            "author",
            "task__assignee",
        ).get(id=comment_id)
    except Comment.DoesNotExist:
        return None

    task = comment.task
    if task.assignee and task.assignee != comment.author:
        notification = Notification.objects.create(
            recipient=task.assignee,
            actor=comment.author,
            verb="commented on",
            target_task=task,
        )
        publish_team_event(
            team_id=task.project.team_id,
            event_type="notification.created",
            payload=notification_payload(notification),
        )
        return notification.id

    return None


@shared_task
def create_assignment_notification(task_id):
    try:
        task = Task.objects.select_related("assignee", "creator").get(id=task_id)
    except Task.DoesNotExist:
        return None

    if task.assignee:
        notification = Notification.objects.create(
            recipient=task.assignee,
            actor=task.creator,
            verb="assigned you to",
            target_task=task,
        )
        publish_team_event(
            team_id=task.project.team_id,
            event_type="notification.created",
            payload=notification_payload(notification),
        )
        return notification.id

    return None