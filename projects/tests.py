import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from .models import Project

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_project_as_admin(api_client):
    user = User.objects.create_user(email="admin@h.com", username="admin", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role='ADMIN')
    
    api_client.force_authenticate(user=user)
    url = reverse('project-list-create', kwargs={'team_id': team.id})
    response = api_client.post(url, {"name": "New API"})
    
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_project_as_member(api_client):
    user = User.objects.create_user(email="mem@h.com", username="mem", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role='MEMBER')
    
    api_client.force_authenticate(user=user)
    url = reverse('project-list-create', kwargs={'team_id': team.id})
    response = api_client.post(url, {"name": "Hacker Project"})
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_get_project_as_member(api_client):
    user = User.objects.create_user(email="mem@h.com", username="mem", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role='MEMBER')
    project = Project.objects.create(team=team, name="Project1")
    
    api_client.force_authenticate(user=user)
    url = reverse('project-list-create', kwargs={'team_id': team.id})
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]['name'] == "Project1"

@pytest.mark.django_db
def test_get_project_as_non_member(api_client):
    user = User.objects.create_user(email="mem@h.com", username="mem", password="pw")
    team = Team.objects.create(name="Dev Team")
    
    api_client.force_authenticate(user=user)
    url = reverse('project-list-create', kwargs={'team_id': team.id})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data['error'] == "You do not have access to this team's projects."
    
