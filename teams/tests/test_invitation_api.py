import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from teams.models import Invitation, Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_invitation_flow(api_client):
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    new_user = User.objects.create_user(email="new@h.com", password="pw")
    team = Team.objects.create(name="Growth Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)

    api_client.force_authenticate(user=admin)
    response = api_client.post(reverse("invite-create", args=[team.id]), {"email": "new@h.com"})

    assert response.status_code == status.HTTP_201_CREATED
    token = response.data["token"]
    invite = Invitation.objects.get(token=token)
    assert invite.accepted_at is None

    api_client.force_authenticate(user=new_user)
    response = api_client.post(reverse("invite-accept", args=[token]))

    assert response.status_code == status.HTTP_200_OK
    assert TeamMembership.objects.filter(user=new_user, team=team).exists()

    invite = Invitation.objects.get(token=token)
    assert invite.accepted_at is not None


@pytest.mark.django_db
def test_invitation_delete(api_client):
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    new_user = User.objects.create_user(email="new@h.com", password="pw")
    team = Team.objects.create(name="Growth Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    api_client.force_authenticate(user=admin)

    response = api_client.post(reverse("invite-create", args=[team.id]), {"email": "new@h.com"})

    assert response.status_code == status.HTTP_201_CREATED
    invite = Invitation.objects.get(token=response.data["token"])

    response = api_client.delete(reverse("invite-delete", args=[team.id, invite.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not TeamMembership.objects.filter(user=new_user, team=team).exists()


@pytest.mark.django_db
def test_cannot_accept_invitation_for_different_email(api_client):
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    wrong_user = User.objects.create_user(email="wrong@h.com", password="pw")
    team = Team.objects.create(name="Private Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)

    invite = Invitation.objects.create(team=team, email="target@h.com", invited_by=admin)

    api_client.force_authenticate(user=wrong_user)
    response = api_client.post(reverse("invite-accept", args=[invite.token]))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not TeamMembership.objects.filter(user=wrong_user, team=team).exists()


@pytest.mark.django_db
def test_invite_user_already_in_team(api_client):
    admin = User.objects.create_user(email="admin@h.com", password="pw")
    member = User.objects.create_user(email="member@h.com", password="pw")
    team = Team.objects.create(name="Full Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)

    api_client.force_authenticate(user=admin)
    response = api_client.post(reverse("invite-create", args=[team.id]), {"email": "member@h.com"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["type"] == "https://taskhive.com/errors/business_logic_violation"