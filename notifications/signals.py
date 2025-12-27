from django.db.models.signals import post_save
from django.dispatch import receiver
from tasks.models import Task
from comments.models import Comment
from .models import Notification

@receiver(post_save, sender=Comment)
def notify_comment(sender, instance, created, **kwargs):
    if created:
        task = instance.task
        if task.assignee and task.assignee != instance.author:
            Notification.objects.create(
                recipient=task.assignee,
                actor=instance.author,
                verb="commented on",
                target_task=task
            )

@receiver(post_save, sender=Task)
def notify_assignment(sender, instance, created, **kwargs):
    if created and instance.assignee:
        Notification.objects.create(
            recipient=instance.assignee,
            actor=instance.creator,
            verb="assigned you to",
            target_task=instance
        )