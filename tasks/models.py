from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel
from projects.models import Project
from teams.models import Team


class Tag(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tags")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "name")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["team", "project", "name"]),
        ]

    def __str__(self):
        return self.name


class Task(SoftDeleteModel):
    class Status(models.TextChoices):
        TODO = "TODO", "To Do"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        DONE = "DONE", "Done"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subtasks")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_tasks")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")
    tags = models.ManyToManyField(Tag, blank=True, related_name="tasks")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)

    position = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["position"]
        indexes = [
            models.Index(fields=["project", "status", "is_deleted"]),
            models.Index(fields=["project", "assignee", "is_deleted"]),
            models.Index(fields=["parent", "is_deleted"]),
            models.Index(fields=["is_deleted", "updated_at"]),
        ]

    def __str__(self):
        return self.title