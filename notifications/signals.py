from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import Comment
from notifications.tasks import create_assignment_notification, create_comment_notification
from tasks.models import Task


@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    if created:
        create_comment_notification.delay(instance.id)


@receiver(post_save, sender=Task)
def notify_assignment(sender, instance, created, **kwargs):
    if created and instance.assignee_id:
        create_assignment_notification.delay(instance.id)