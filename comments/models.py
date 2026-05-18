from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel
from tasks.models import Task


class Comment(SoftDeleteModel):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["task", "is_deleted", "created_at"]),
        ]