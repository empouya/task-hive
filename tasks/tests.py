import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from projects.models import Project

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_task_by_admin(api_client):
    # Setup Team
    admin = User.objects.create_user(email="admin@a.com", username="admin", password="pw")
    member = User.objects.create_user(email="member@a.com", username="member", password="pw")
    team_a = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team_a, role='ADMIN')
    TeamMembership.objects.create(user=member, team=team_a, role='MEMBER')
    project = Project.objects.create(team=team_a, name="Internal Proj")
    
    # Task creation by admin
    api_client.force_authenticate(user=admin)
    url = reverse('task-create', kwargs={'project_id': project.id})
    
    response = api_client.post(url, {"title": "new task", "assignee": member.id})
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "new task" in str(response.data)

@pytest.mark.django_db
def test_create_task_by_member(api_client):
    # Setup Team
    admin = User.objects.create_user(email="admin@a.com", username="admin", password="pw")
    member = User.objects.create_user(email="member@a.com", username="member", password="pw")
    team_a = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team_a, role='ADMIN')
    TeamMembership.objects.create(user=member, team=team_a, role='MEMBER')
    project = Project.objects.create(team=team_a, name="Internal Proj")
    
    # Task creation by admin
    api_client.force_authenticate(user=admin)
    url = reverse('task-create', kwargs={'project_id': project.id})
    
    response = api_client.post(url, {"title": "new task",})
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "new task" in str(response.data)
    

@pytest.mark.django_db
def test_create_task_by_not_a_member(api_client):
    """A user from Team B cannot be assigned a task in Team A."""
    # Setup Team and Admin
    admin = User.objects.create_user(email="admin@a.com", username="admin", password="pw")
    team_a = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team_a, role='ADMIN')
    project = Project.objects.create(team=team_a, name="Internal Proj")
    
    # Setup Stranger
    stranger = User.objects.create_user(email="stranger@a.com", username="stranger", password="pw")
    
    api_client.force_authenticate(user=stranger)
    url = reverse('task-create', kwargs={'project_id': project.id})
    
    response = api_client.post(url, {"title": "hack Task",})
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "You are not a member of this team." in str(response.data)

@pytest.mark.django_db
def test_create_task_to_archived_project(api_client):
    """A user from Team B cannot be assigned a task in Team A."""
    # Setup Team and Admin
    admin = User.objects.create_user(email="admin@a.com", username="admin", password="pw")
    team_a = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team_a, role='ADMIN')
    project = Project.objects.create(team=team_a, name="Internal Proj")
    project.status = Project.Status.ARCHIVED
    project.save()

    api_client.force_authenticate(user=admin)
    url = reverse('task-create', kwargs={'project_id': project.id})
    
    response = api_client.post(url, {"title": "new task",})
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot create tasks in an archived project." in str(response.data)
    
@pytest.mark.django_db
def test_create_task_invalid_assignee(api_client):
    """A user from Team B cannot be assigned a task in Team A."""
    # Setup Team A and Admin
    admin = User.objects.create_user(email="admin@a.com", username="admin", password="pw")
    team_a = Team.objects.create(name="Team A")
    TeamMembership.objects.create(user=admin, team=team_a, role='ADMIN')
    project = Project.objects.create(team=team_a, name="Internal Proj")
    
    # Setup Stranger from Team B
    stranger = User.objects.create_user(email="stranger@b.com", username="stranger", password="pw")
    
    api_client.force_authenticate(user=admin)
    url = reverse('task-create', kwargs={'project_id': project.id})
    
    response = api_client.post(url, {
        "title": "Invader Task",
        "assignee": stranger.id
    })
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Assignee must be a member of the team" in str(response.data)