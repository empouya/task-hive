from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel
from common.storage import attachment_upload_to
from tasks.models import Task
from teams.models import Team


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


class CommentAttachment(SoftDeleteModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="comment_attachments")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_attachments")
    file = models.FileField(upload_to=attachment_upload_to)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["team", "comment", "is_deleted"]),
            models.Index(fields=["uploaded_by", "is_deleted"]),
        ]

    def __str__(self):
        return self.original_filename