import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from projects.models import Project
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_removed_user_tasks_become_unassigned(api_client):
    admin = User.objects.create_user(email="a@h.com")
    member = User.objects.create_user(email="m@h.com")
    team = Team.objects.create(name="Cleanup Crew")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, assignee=member, title="Fix")

    api_client.force_authenticate(user=admin)
    api_client.delete(reverse("team-member-remove", kwargs={"team_id": team.id, "user_id": member.id}))

    task.refresh_from_db()
    assert task.assignee is None
    assert not TeamMembership.objects.filter(user=member, team=team).exists()


@pytest.mark.django_db
def test_cannot_remove_last_owner(api_client):
    owner = User.objects.create_user(email="last_owner@h.com", password="pw")
    team = Team.objects.create(name="Lonely Team")
    TeamMembership.objects.create(user=owner, team=team, role=TeamMembership.Role.OWNER)

    api_client.force_authenticate(user=owner)
    response = api_client.delete(reverse("team-member-remove", kwargs={"team_id": team.id, "user_id": owner.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["type"] == "https://taskhive.com/errors/business_logic_violation"
    assert TeamMembership.objects.filter(user=owner, team=team).exists()


@pytest.mark.django_db
def test_admin_cannot_remove_owner(api_client):
    owner = User.objects.create_user(email="owner@h.com", password="pw")
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Owner Protected")
    TeamMembership.objects.create(user=owner, team=team, role=TeamMembership.Role.OWNER)
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)

    api_client.force_authenticate(user=admin)
    response = api_client.delete(reverse("team-member-remove", kwargs={"team_id": team.id, "user_id": owner.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert TeamMembership.objects.filter(user=owner, team=team).exists()