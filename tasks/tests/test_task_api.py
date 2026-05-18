import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from projects.models import Project
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_task_by_admin(api_client):
    admin = User.objects.create_user(email="admin@a.com", password="pw")
    member = User.objects.create_user(email="member@a.com", password="pw")
    team = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="Internal Proj")

    api_client.force_authenticate(user=admin)
    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "new task", "assignee": member.id})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "new task"


@pytest.mark.django_db
def test_create_task_by_member(api_client):
    member = User.objects.create_user(email="member@a.com", password="pw")
    team = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="Internal Proj")

    api_client.force_authenticate(user=member)
    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "new task"})

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "new task"


@pytest.mark.django_db
def test_viewer_cannot_create_task(api_client):
    viewer = User.objects.create_user(email="viewer@a.com", password="pw")
    team = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=viewer, team=team, role=TeamMembership.Role.VIEWER)
    project = Project.objects.create(team=team, name="Internal Proj")

    api_client.force_authenticate(user=viewer)
    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "blocked task"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_create_task_by_not_a_member(api_client):
    admin = User.objects.create_user(email="admin@a.com", password="pw")
    team = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Internal Proj")
    stranger = User.objects.create_user(email="stranger@a.com", password="pw")

    api_client.force_authenticate(user=stranger)
    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "hack Task"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not a member" in response.data["detail"]


@pytest.mark.django_db
def test_create_task_to_archived_project(api_client):
    admin = User.objects.create_user(email="admin@a.com", password="pw")
    team = Team.objects.create(name="Our Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Internal Proj", status=Project.Status.ARCHIVED)

    api_client.force_authenticate(user=admin)
    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "new task"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "archived project" in response.data["detail"].lower()


@pytest.mark.django_db
def test_create_task_invalid_assignee(api_client):
    admin = User.objects.create_user(email="admin@a.com", password="pw")
    team = Team.objects.create(name="Team A")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Internal Proj")
    stranger = User.objects.create_user(email="stranger@b.com", password="pw")

    api_client.force_authenticate(user=admin)
    response = api_client.post(
        reverse("task-create-list", kwargs={"project_id": project.id}),
        {"title": "Invader Task", "assignee": stranger.id},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Assignee must be a member of the team" in response.data["detail"]


@pytest.mark.django_db
def test_task_reordering_logic(api_client):
    user = User.objects.create_user(email="ranker@h.com", password="pw")
    team = Team.objects.create(name="Rank Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="Board")
    task1 = Task.objects.create(project=project, creator=user, title="Task 1", position=1.0)
    task2 = Task.objects.create(project=project, creator=user, title="Task 2", position=2.0)

    api_client.force_authenticate(user=user)
    response = api_client.patch(reverse("task-reorder", kwargs={"task_id": task2.id}), {"position": 0.5})

    assert response.status_code == status.HTTP_200_OK

    tasks = Task.objects.filter(project=project).order_by("position")
    assert tasks[0].title == "Task 2"
    assert tasks[1].title == "Task 1"


@pytest.mark.django_db
def test_update_task(api_client):
    user = User.objects.create_user(email="u1@h.com")
    team = Team.objects.create(name="Dev")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="To be updated")
    api_client.force_authenticate(user=user)

    response = api_client.patch(reverse("task-detail", kwargs={"task_id": task.id}), {"title": "Updated!", "status": Task.Status.DONE})

    task.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert task.title == "Updated!"
    assert task.status == Task.Status.DONE


@pytest.mark.django_db
def test_task_delete_soft_deletes(api_client):
    user = User.objects.create_user(email="u1@h.com")
    team = Team.objects.create(name="Dev")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="To be updated")
    api_client.force_authenticate(user=user)

    response = api_client.delete(reverse("task-detail", kwargs={"task_id": task.id}))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Task.objects.filter(id=task.id).exists()
    assert Task.all_objects.filter(id=task.id, is_deleted=True).exists()


@pytest.mark.django_db
def test_reassign_task(api_client):
    user = User.objects.create_user(email="m@h.com")
    admin = User.objects.create_user(email="a@h.com")
    team = Team.objects.create(name="Dev")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, title="Work")

    api_client.force_authenticate(user=user)
    response = api_client.patch(reverse("task-assign", kwargs={"task_id": task.id}), {"assignee_id": user.id})

    task.refresh_from_db()
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert task.assignee is None

    api_client.force_authenticate(user=admin)
    response = api_client.patch(reverse("task-assign", kwargs={"task_id": task.id}), {"assignee_id": user.id})

    task.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert task.assignee_id == user.id


@pytest.mark.django_db
def test_list_task(api_client):
    admin = User.objects.create_user(email="a@h.com")
    team = Team.objects.create(name="Dev")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="P1")
    Task.objects.create(project=project, creator=admin, title="Task 1", position=2.0)
    Task.objects.create(project=project, creator=admin, title="Task 2", position=1.0)
    Task.objects.create(project=project, creator=admin, title="Task 3", position=3.0)
    api_client.force_authenticate(user=admin)

    response = api_client.get(reverse("task-create-list", kwargs={"project_id": project.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["title"] == "Task 2"
    assert response.data[1]["title"] == "Task 1"
    assert response.data[2]["title"] == "Task 3"


@pytest.mark.django_db
class TestTaskHarden:
    def test_list_tasks_access_denied_for_non_members(self, api_client):
        owner = User.objects.create_user(email="owner@h.com", password="pw")
        stranger = User.objects.create_user(email="stranger@h.com", password="pw")
        team = Team.objects.create(name="Private Team")
        TeamMembership.objects.create(user=owner, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="Secret Roadmap")
        Task.objects.create(project=project, creator=owner, title="Sensitive Task")

        api_client.force_authenticate(user=stranger)
        response = api_client.get(reverse("task-create-list", kwargs={"project_id": project.id}))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_delete_task_in_archived_project(self, api_client):
        admin = User.objects.create_user(email="admin@h.com", password="pw")
        team = Team.objects.create(name="Old Team")
        TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="Old Project", status=Project.Status.ARCHIVED)
        task = Task.objects.create(project=project, creator=admin, title="Old Task")

        api_client.force_authenticate(user=admin)
        response = api_client.delete(reverse("task-detail", kwargs={"task_id": task.id}))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Task.objects.filter(id=task.id).exists()

    def test_cannot_reorder_task_in_archived_project(self, api_client):
        admin = User.objects.create_user(email="admin@h.com", password="pw")
        team = Team.objects.create(name="Old Team")
        TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="Old Project", status=Project.Status.ARCHIVED)
        task = Task.objects.create(project=project, creator=admin, title="Task", position=1.0)

        api_client.force_authenticate(user=admin)
        response = api_client.patch(reverse("task-reorder", kwargs={"task_id": task.id}), {"position": 2.0})

        assert response.status_code == status.HTTP_403_FORBIDDEN