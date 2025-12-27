from django.db import models
from teams.models import Team

class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ARCHIVED = 'ARCHIVED', 'Archived'

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team.name} | {self.name}"
