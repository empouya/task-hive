from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

class TeamManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # team manager will filter out the deleted rows
    objects = TeamManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def __str__(self):
        return self.name

class TeamMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MEMBER = 'MEMBER', 'Member'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'team')

class Invitation(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
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
