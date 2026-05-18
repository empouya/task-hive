import pytest
from django.contrib.auth import get_user_model

from common.exceptions import PermissionDeniedError
from teams import services
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_team_assigns_owner_role():
    user = User.objects.create_user(email="creator@h.com", password="pw")

    team = services.create_team(
        user=user,
        data={"name": "Owned Team", "description": "Created through service"},
    )

    assert team.name == "Owned Team"
    assert TeamMembership.objects.filter(
        user=user,
        team=team,
        role=TeamMembership.Role.OWNER,
    ).exists()


@pytest.mark.django_db
def test_member_cannot_soft_delete_team_from_service():
    member = User.objects.create_user(email="member-service@h.com", password="pw")
    team = Team.objects.create(name="Service Team")
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)

    with pytest.raises(PermissionDeniedError):
        services.soft_delete_team(user=member, team_id=team.id)

    assert Team.objects.filter(id=team.id).exists()