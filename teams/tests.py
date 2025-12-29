import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import TeamMembership, Team, Invitation
from projects.models import Project
from tasks.models import Task

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_team_authenticated(api_client):
    user = User.objects.create_user(email="boss@hive.com", password="pw")
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
    me = User.objects.create_user(email="me@h.com", password="pw")
    other = User.objects.create_user(email="other@h.com", password="pw")
    
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
    user = User.objects.create_user(email="admin@h.com", password="pw")
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
    user = User.objects.create_user(email="admin@h.com", password="pw")
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

@pytest.mark.django_db
def test_invitation_flow(api_client):
    # Setup
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    new_user = User.objects.create_user(email="new@h.com", password="pw")
    team = Team.objects.create(name="Growth Team")
    TeamMembership.objects.create(user=admin, team=team, role='ADMIN')

    # Admin Invites User
    api_client.force_authenticate(user=admin)
    res = api_client.post(reverse('invite-create', args=[team.id]), {"email": "new@h.com"})

    # Test 1
    assert res.status_code == 201
    token = res.data['token']
    invite = Invitation.objects.get(token=token)
    assert invite.accepted_at is None

    # New User Accepts
    api_client.force_authenticate(user=new_user)
    accept_url = reverse('invite-accept', args=[token])
    res = api_client.post(accept_url)

    # Test 2
    assert res.status_code == 200
    assert TeamMembership.objects.filter(user=new_user, team=team).exists()
    invite = Invitation.objects.get(token=token)
    assert invite.accepted_at is not None

@pytest.mark.django_db
def test_invitation_delete(api_client):
    # Setup
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    new_user = User.objects.create_user(email="new@h.com", password="pw")
    team = Team.objects.create(name="Growth Team")
    TeamMembership.objects.create(user=admin, team=team, role='ADMIN')
    api_client.force_authenticate(user=admin)

    # Admin Invites User
    res = api_client.post(reverse('invite-create', args=[team.id]), {"email": "new@h.com"})

    # Test 1
    assert res.status_code == 201
    token = res.data['token']
    invite = Invitation.objects.get(token=token)
    assert invite.accepted_at is None

    # Admin Cancels invitation
    accept_url = reverse('invite-delete', args=[team.id, invite.id])
    res = api_client.delete(accept_url)

    # Test 2
    assert res.status_code == 204
    assert not TeamMembership.objects.filter(user=new_user, team=team).exists()

@pytest.mark.django_db
def test_removed_user_tasks_become_unassigned(api_client):
    # Setup
    admin = User.objects.create_user(email="a@h.com")
    member = User.objects.create_user(email="m@h.com")
    team = Team.objects.create(name="Cleanup Crew")
    TeamMembership.objects.create(user=admin, team=team, role='ADMIN')
    TeamMembership.objects.create(user=member, team=team, role='MEMBER')
    proj = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=proj, creator=admin, assignee=member, title="Fix")

    # API call
    api_client.force_authenticate(user=admin)
    url = reverse('team-member-remove', kwargs={'team_id': team.id, 'user_id': member.id})
    api_client.delete(url)

    # Test
    task.refresh_from_db()
    assert task.assignee is None
    assert not TeamMembership.objects.filter(user=member, team=team).exists()

@pytest.mark.django_db
class TestTeamSecurityHarden:
    
    def test_member_cannot_delete_team(self, api_client):
        """Only ADMINs should be allowed to soft-delete a team."""
        user = User.objects.create_user(email="member@h.com", password="pw")
        team = Team.objects.create(name="Secure Team")
        TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
        
        api_client.force_authenticate(user=user)
        url = reverse('team-detail', kwargs={'team_id': team.id})
        response = api_client.delete(url)
        
        assert response.status_code == 403
        assert Team.objects.filter(id=team.id).exists()

    def test_cannot_remove_last_admin(self, api_client):
        """A team must always have at least one admin."""
        admin = User.objects.create_user(email="last_admin@h.com", password="pw")
        team = Team.objects.create(name="Lonely Team")
        TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
        
        api_client.force_authenticate(user=admin)
        url = reverse('team-member-remove', kwargs={'team_id': team.id, 'user_id': admin.id})
        response = api_client.delete(url)
        
        assert response.status_code == 400
        assert "last admin" in response.data['error'].lower()

@pytest.mark.django_db
class TestInvitationHarden:

    def test_cannot_accept_invitation_for_different_email(self, api_client):
        """Invitations are bound to specific email addresses."""
        admin = User.objects.create_user(email="admin@h.com", password="pw")
        wrong_user = User.objects.create_user(email="wrong@h.com", password="pw")
        team = Team.objects.create(name="Private Team")
        TeamMembership.objects.create(user=admin, team=team, role='ADMIN')
        
        # Invite intended for 'target@h.com'
        invite = Invitation.objects.create(team=team, email="target@h.com", invited_by=admin)
        
        api_client.force_authenticate(user=wrong_user)
        url = reverse('invite-accept', args=[invite.token])
        response = api_client.post(url)
        
        assert response.status_code == 403
        assert not TeamMembership.objects.filter(user=wrong_user, team=team).exists()

    def test_invite_user_already_in_team(self, api_client):
        """Prevent redundant invitations for existing members."""
        admin = User.objects.create_user(email="admin@h.com", password="pw")
        member = User.objects.create_user(email="member@h.com", password="pw")
        team = Team.objects.create(name="Full Team")
        TeamMembership.objects.create(user=admin, team=team, role='ADMIN')
        TeamMembership.objects.create(user=member, team=team, role='MEMBER')
        
        api_client.force_authenticate(user=admin)
        url = reverse('invite-create', args=[team.id])
        response = api_client.post(url, {"email": "member@h.com"})
        
        assert response.status_code == 400
        assert "already a member" in response.data['error'].lower()
