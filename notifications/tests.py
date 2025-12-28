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

    # Assert: User B should have a notification
    assert Notification.objects.filter(recipient=user_b, actor=user_a).exists()

@pytest.mark.django_db
def test_notification_list(api_client):
    # Setup
    user_a = User.objects.create_user(username="user_a", email="a@h.com")
    user_b = User.objects.create_user(username="user_b", email="b@h.com")
    team = Team.objects.create(name="T1")
    proj = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=proj, creator=user_a, title="Task")
    Notification.objects.create(recipient=user_b, actor=user_a, verb="developed", target_task=task)
    Notification.objects.create(recipient=user_b, actor=user_a, verb="tested", target_task=task)

    # API call
    api_client.force_authenticate(user=user_b)
    url = reverse('notification-list')
    response = api_client.get(url)
    
    # Test
    assert response.status_code == 200
    assert len(response.data) == 2

@pytest.mark.django_db
def test_notification_read(api_client):
    user_a = User.objects.create_user(username="user_a", email="a@h.com")
    user_b = User.objects.create_user(username="user_b", email="b@h.com")
    team = Team.objects.create(name="T1")
    proj = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=proj, creator=user_a, title="Task")
    note = Notification.objects.create(recipient=user_b, actor=user_a, verb="tested", target_task=task)

    # API call (Not owner)
    api_client.force_authenticate(user=user_a)
    url = reverse('notification-read', kwargs={'notification_id': note.id})
    response = api_client.patch(url)

    # Test (Not owner)
    assert response.status_code == 404 
    
    # API call (Owner)
    api_client.force_authenticate(user=user_b)
    response = api_client.patch(url)
    
    # Test (Owner)
    note.refresh_from_db()
    assert response.status_code == 200
    assert note.unread is False
