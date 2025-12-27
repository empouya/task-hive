from django.db import models
from django.conf import settings
from tasks.models import Task


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verb = models.CharField(max_length=255)
    target_task = models.ForeignKey(Task, on_delete=models.CASCADE)
    unread = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
