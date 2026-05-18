from datetime import timedelta
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.models import SoftDeleteModel


class Team(SoftDeleteModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_deleted", "created_at"]),
        ]

    def __str__(self):
        return self.name

class TeamMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        MEMBER = "MEMBER", "Member"
        VIEWER = "VIEWER", "Viewer"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "team")
        indexes = [
            models.Index(fields=["team", "role"]),
            models.Index(fields=["user", "role"]),
        ]


class Invitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        expiry_date = self.created_at + timedelta(days=1)
        return self.accepted_at is None and timezone.now() < expiry_date

    def __str__(self):
        return f"Invite to {self.email} for {self.team.name}"