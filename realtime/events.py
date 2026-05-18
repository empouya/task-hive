from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def publish_team_event(*, team_id, event_type, payload):
    channel_layer = get_channel_layer()

    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"team.{team_id}",
        {
            "type": "team.event",
            "payload": {
                "type": event_type,
                **payload,
            },
        },
    )


def task_payload(task):
    return {
        "task": {
            "id": task.id,
            "project_id": task.project_id,
            "title": task.title,
            "status": task.status,
            "position": str(task.position),
            "assignee_id": task.assignee_id,
            "parent_id": task.parent_id,
        }
    }


def comment_payload(comment):
    return {
        "comment": {
            "id": comment.id,
            "task_id": comment.task_id,
            "author_id": comment.author_id,
            "created_at": comment.created_at.isoformat(),
        }
    }


def notification_payload(notification):
    return {
        "notification": {
            "id": notification.id,
            "recipient_id": notification.recipient_id,
            "actor_id": notification.actor_id,
            "verb": notification.verb,
            "target_task_id": notification.target_task_id,
            "created_at": notification.created_at.isoformat(),
        }
    }