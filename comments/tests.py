import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from projects.models import Project
from .models import Comment
from tasks.models import Task
User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_task_reordering_logic(api_client):
    # Setup
    user1 = User.objects.create_user(email="user1@h.com", username="user1", password="pw")
    user2 = User.objects.create_user(email="user2@h.com", username="user2", password="pw")
    team = Team.objects.create(name="Comment Team")
    TeamMembership.objects.create(user=user1, team=team)
    TeamMembership.objects.create(user=user2, team=team)
    project = Project.objects.create(team=team, name="Board")
    
    task1 = Task.objects.create(project=project, creator=user1, title="Task 1", position=1.0)
    task2 = Task.objects.create(project=project, creator=user2, title="Task 2", position=2.0)
    
    api_client.force_authenticate(user=user2)
    
    url = reverse('comment-create-list', kwargs={'task_id': task1.id})
    response = api_client.post(url, {"content": "This task is so cool!"})
    assert response.status_code == 201
    
    comment = get_object_or_404(Comment, id=response.data['id'])
    assert comment.content == "This task is so cool!"
    assert comment.task_id == 1
    assert comment.author_id == 2

@pytest.mark.django_db
def test_delete_comment(api_client):
    # Setup
    admin = User.objects.create_user(username="admin", email="a@h.com")
    member = User.objects.create_user(username="member", email="m@h.com")
    team = Team.objects.create(name="Mod Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, title="Task")
    comment = Comment.objects.create(task=task, author=member, content="Delete me if you can!")
    url = reverse('comment-detail', kwargs={'comment_id': comment.id})

    # API call (Member)
    api_client.force_authenticate(user=member)
    response = api_client.delete(url)

    # Test (Member)
    assert response.status_code == 403
    assert Comment.objects.filter(id=comment.id).exists()

    #  API call (Admin)
    api_client.force_authenticate(user=admin)
    response = api_client.delete(url)

    # Test (Admin)
    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment.id).exists()
