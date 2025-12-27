import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import TeamMembership, Team

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_team_authenticated(api_client):
    user = User.objects.create_user(email="boss@hive.com", username="boss", password="pw")
    api_client.force_authenticate(user=user)
    
    url = reverse('team-list-create')
    data = {"name": "Engineers", "description": "Build things"}
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED

    # Check that membership was created automatically
    assert TeamMembership.objects.filter(user=user, role='ADMIN').exists()

@pytest.mark.django_db
def test_list_user_teams(api_client):
    """
    Test that a user only sees teams they are a member of, 
    even with multiple teams and different roles.
    """
    # 1. Setup: Two Users
    me = User.objects.create_user(email="me@h.com", username="me", password="pw")
    other = User.objects.create_user(email="other@h.com", username="other", password="pw")
    
    # 2. Setup: Teams
    from teams.models import Team, TeamMembership
    
    # Team A: I am an ADMIN
    team_a = Team.objects.create(name="Team A", description="I lead this")
    TeamMembership.objects.create(user=me, team=team_a, role=TeamMembership.Role.ADMIN)
    
    # Team B: I am a MEMBER
    team_b = Team.objects.create(name="Team B", description="I follow here")
    TeamMembership.objects.create(user=me, team=team_b, role=TeamMembership.Role.MEMBER)
    
    # Team C: Someone else's team (I should NOT see this)
    team_c = Team.objects.create(name="Team C")
    TeamMembership.objects.create(user=other, team=team_c, role=TeamMembership.Role.ADMIN)
    
    # 3. Execution
    api_client.force_authenticate(user=me)
    url = reverse('team-list-create')
    response = api_client.get(url)
    
    # 4. Assertions
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    
    # Verify the specific teams are present by name
    team_names = [item['name'] for item in response.data]
    assert "Team A" in team_names
    assert "Team B" in team_names
    assert "Team C" not in team_names

@pytest.mark.django_db
def test_update_team_as_admin(api_client):
    # Setup
    user = User.objects.create_user(email="admin@h.com", username="admin", password="pw")
    team = Team.objects.create(name="To Be Updated")
    TeamMembership.objects.create(user=user, team=team, role='ADMIN')
    api_client.force_authenticate(user=user)

    # API call
    url = reverse('team-detail', kwargs={'team_id': team.id})
    response = api_client.patch(url, {"name":"Updated"})

    # Test
    team.refresh_from_db()
    assert response.status_code == 200
    assert team.name == "Updated"

@pytest.mark.django_db
def test_soft_delete_team_as_admin(api_client):
    # Setup
    user = User.objects.create_user(email="admin@h.com", username="admin", password="pw")
    team = Team.objects.create(name="To Be Deleted")
    TeamMembership.objects.create(user=user, team=team, role='ADMIN')
    api_client.force_authenticate(user=user)

    # API call
    url = reverse('team-detail', kwargs={'team_id': team.id})
    response = api_client.delete(url)

    # Test
    assert response.status_code == 204
    assert Team.objects.filter(id=team.id).count() == 0
    assert Team.all_objects.filter(id=team.id).count() == 1
