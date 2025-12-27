import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from projects.models import Project
from tasks.models import Task
from comments.models import Comment
from .models import Notification

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_notification_created_on_comment(api_client):
    # Setup: User A creates a task and assigns it to User B
    user_a = User.objects.create_user(email="a@h.com", username="a", password="pw")
    user_b = User.objects.create_user(email="b@h.com", username="b", password="pw")
    team = Team.objects.create(name="Notify Team")
    TeamMembership.objects.create(user=user_a, team=team)
    TeamMembership.objects.create(user=user_b, team=team)
    
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user_a, assignee=user_b, title="T1")

    # Action: User A comments
    api_client.force_authenticate(user=user_a)
    url = reverse('create-comment', kwargs={'task_id': task.id})
    api_client.post(url, {"content": "Checking in!"})

    for notif in Notification.objects.all():
        print(notif.__dict__)

    # Assert: User B should have a notification
    assert Notification.objects.filter(recipient=user_b, actor=user_a).exists()
