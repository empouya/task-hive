import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_team_authenticated(api_client):
    user = User.objects.create_user(email="boss@hive.com", password="pw")
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("team-list-create"),
        {"name": "Engineers", "description": "Build things"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert TeamMembership.objects.filter(
        user=user,
        role=TeamMembership.Role.OWNER,
    ).exists()


@pytest.mark.django_db
def test_list_user_teams(api_client):
    me = User.objects.create_user(email="me@h.com", password="pw")
    other = User.objects.create_user(email="other@h.com", password="pw")

    team_a = Team.objects.create(name="Team A", description="I lead this")
    TeamMembership.objects.create(user=me, team=team_a, role=TeamMembership.Role.ADMIN)

    team_b = Team.objects.create(name="Team B", description="I follow here")
    TeamMembership.objects.create(user=me, team=team_b, role=TeamMembership.Role.MEMBER)

    team_c = Team.objects.create(name="Team C")
    TeamMembership.objects.create(user=other, team=team_c, role=TeamMembership.Role.ADMIN)

    api_client.force_authenticate(user=me)
    response = api_client.get(reverse("team-list-create"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    team_names = [item["name"] for item in response.data]
    assert "Team A" in team_names
    assert "Team B" in team_names
    assert "Team C" not in team_names


@pytest.mark.django_db
def test_update_team_as_admin(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="To Be Updated")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    api_client.force_authenticate(user=user)

    response = api_client.patch(reverse("team-detail", kwargs={"team_id": team.id}), {"name": "Updated"})

    team.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert team.name == "Updated"


@pytest.mark.django_db
def test_soft_delete_team_as_admin(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="To Be Deleted")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    api_client.force_authenticate(user=user)

    response = api_client.delete(reverse("team-detail", kwargs={"team_id": team.id}))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Team.objects.filter(id=team.id).count() == 0
    assert Team.all_objects.filter(id=team.id).count() == 1


@pytest.mark.django_db
def test_member_cannot_delete_team(api_client):
    user = User.objects.create_user(email="member@h.com", password="pw")
    team = Team.objects.create(name="Secure Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)

    api_client.force_authenticate(user=user)
    response = api_client.delete(reverse("team-detail", kwargs={"team_id": team.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Team.objects.filter(id=team.id).exists()