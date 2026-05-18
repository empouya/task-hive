import pytest
from django.contrib.auth import get_user_model

from common.permissions import (
    can_comment,
    can_manage_members,
    can_manage_projects,
    can_manage_team,
    can_read_team,
    can_reorder_tasks,
    can_write_tasks,
)
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (TeamMembership.Role.OWNER, True),
        (TeamMembership.Role.ADMIN, True),
        (TeamMembership.Role.MANAGER, False),
        (TeamMembership.Role.MEMBER, False),
        (TeamMembership.Role.VIEWER, False),
    ],
)
def test_team_management_permissions(role, expected):
    user = User.objects.create_user(email=f"{role.lower()}@taskhive.com", password="pw")
    team = Team.objects.create(name=f"{role} Team")
    TeamMembership.objects.create(user=user, team=team, role=role)

    assert can_manage_team(user, team) is expected
    assert can_manage_members(user, team) is expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "can_write"),
    [
        (TeamMembership.Role.OWNER, True),
        (TeamMembership.Role.ADMIN, True),
        (TeamMembership.Role.MANAGER, True),
        (TeamMembership.Role.MEMBER, True),
        (TeamMembership.Role.VIEWER, False),
    ],
)
def test_workspace_write_permissions(role, can_write):
    user = User.objects.create_user(email=f"workspace-{role.lower()}@taskhive.com", password="pw")
    team = Team.objects.create(name=f"Workspace {role}")
    TeamMembership.objects.create(user=user, team=team, role=role)

    assert can_read_team(user, team) is True
    assert can_manage_projects(user, team) is (role in [
        TeamMembership.Role.OWNER,
        TeamMembership.Role.ADMIN,
        TeamMembership.Role.MANAGER,
    ])
    assert can_write_tasks(user, team) is can_write
    assert can_reorder_tasks(user, team) is can_write
    assert can_comment(user, team) is can_write


@pytest.mark.django_db
def test_non_member_has_no_team_permissions():
    user = User.objects.create_user(email="outside@taskhive.com", password="pw")
    team = Team.objects.create(name="Private Team")

    assert can_read_team(user, team) is False
    assert can_manage_team(user, team) is False
    assert can_manage_projects(user, team) is False
    assert can_write_tasks(user, team) is False
    assert can_comment(user, team) is False