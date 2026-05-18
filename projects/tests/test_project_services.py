import pytest
from django.contrib.auth import get_user_model

from common.exceptions import PermissionDeniedError
from projects import services
from projects.models import Project
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_manager_can_create_project():
    user = User.objects.create_user(email="manager-project@h.com", password="pw")
    team = Team.objects.create(name="Project Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MANAGER)

    project = services.create_project(
        user=user,
        team_id=team.id,
        data={"name": "Managed Project"},
    )

    assert project.name == "Managed Project"
    assert project.team == team


@pytest.mark.django_db
def test_viewer_cannot_create_project():
    user = User.objects.create_user(email="viewer-project@h.com", password="pw")
    team = Team.objects.create(name="Viewer Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.VIEWER)

    with pytest.raises(PermissionDeniedError):
        services.create_project(
            user=user,
            team_id=team.id,
            data={"name": "Blocked Project"},
        )


@pytest.mark.django_db
def test_soft_delete_project_hides_from_default_manager():
    user = User.objects.create_user(email="project-delete@h.com", password="pw")
    team = Team.objects.create(name="Delete Project Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Deleted Later")

    services.soft_delete_project(user=user, project_id=project.id)

    assert not Project.objects.filter(id=project.id).exists()
    assert Project.all_objects.filter(id=project.id, is_deleted=True).exists()