import pytest
from django.contrib.auth import get_user_model

from common.exceptions import BusinessLogicError, PermissionDeniedError
from projects.models import Project
from tasks import services
from tasks.models import Tag, Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_subtask_in_same_project():
    user = User.objects.create_user(email="subtask@h.com", password="pw")
    team = Team.objects.create(name="Subtask Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="Board")
    parent = Task.objects.create(project=project, creator=user, title="Parent")

    child = services.create_task(
        user=user,
        project_id=project.id,
        data={
            "title": "Child",
            "parent": parent,
        },
    )

    assert child.parent == parent
    assert list(parent.subtasks.all()) == [child]


@pytest.mark.django_db
def test_create_subtask_rejects_cross_project_parent():
    user = User.objects.create_user(email="cross-parent@h.com", password="pw")
    team = Team.objects.create(name="Cross Parent Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project_a = Project.objects.create(team=team, name="A")
    project_b = Project.objects.create(team=team, name="B")
    parent = Task.objects.create(project=project_b, creator=user, title="Wrong Parent")

    with pytest.raises(BusinessLogicError):
        services.create_task(
            user=user,
            project_id=project_a.id,
            data={
                "title": "Child",
                "parent": parent,
            },
        )


@pytest.mark.django_db
def test_task_tags_are_project_scoped():
    user = User.objects.create_user(email="tagger@h.com", password="pw")
    team = Team.objects.create(name="Tag Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MANAGER)
    project = Project.objects.create(team=team, name="Board")

    tag = services.create_tag(
        user=user,
        project_id=project.id,
        name="Backend",
        color="#2563eb",
    )
    task = services.create_task(
        user=user,
        project_id=project.id,
        data={
            "title": "Tagged Task",
            "tags": [tag],
        },
    )

    assert tag.team == team
    assert tag.project == project
    assert list(task.tags.all()) == [tag]


@pytest.mark.django_db
def test_viewer_cannot_create_task():
    user = User.objects.create_user(email="viewer-task@h.com", password="pw")
    team = Team.objects.create(name="Viewer Task Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.VIEWER)
    project = Project.objects.create(team=team, name="Board")

    with pytest.raises(PermissionDeniedError):
        services.create_task(
            user=user,
            project_id=project.id,
            data={"title": "Nope"},
        )