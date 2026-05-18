import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from projects.models import Project
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_project_as_admin(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)

    api_client.force_authenticate(user=user)
    response = api_client.post(reverse("project-create-list", kwargs={"team_id": team.id}), {"name": "New API"})

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_project_as_manager(api_client):
    user = User.objects.create_user(email="manager@h.com", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MANAGER)

    api_client.force_authenticate(user=user)
    response = api_client.post(reverse("project-create-list", kwargs={"team_id": team.id}), {"name": "Manager API"})

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_project_as_member(api_client):
    user = User.objects.create_user(email="mem@h.com", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)

    api_client.force_authenticate(user=user)
    response = api_client.post(reverse("project-create-list", kwargs={"team_id": team.id}), {"name": "Hacker Project"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_get_project_as_member(api_client):
    user = User.objects.create_user(email="mem@h.com", password="pw")
    team = Team.objects.create(name="Dev Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    Project.objects.create(team=team, name="Project1")

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("project-create-list", kwargs={"team_id": team.id}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Project1"


@pytest.mark.django_db
def test_get_project_as_non_member(api_client):
    user = User.objects.create_user(email="mem@h.com", password="pw")
    team = Team.objects.create(name="Dev Team")

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("project-create-list", kwargs={"team_id": team.id}))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["type"] == "https://taskhive.com/errors/permission_denied"
    assert response.data["detail"] == "You do not have access to this team's projects."


@pytest.mark.django_db
def test_project_update(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Engineering")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Project to be updated")
    api_client.force_authenticate(user=user)

    response = api_client.patch(reverse("project-detail", kwargs={"project_id": project.id}), {"name": "Updated!"})

    project.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert project.name == "Updated!"

    response = api_client.patch(reverse("project-detail", kwargs={"project_id": project.id}), {"status": Project.Status.ARCHIVED})

    project.refresh_from_db()
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["type"] == "https://taskhive.com/errors/business_logic_violation"
    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_archived_project(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Engineering")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Project")
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("project-archive", kwargs={"project_id": project.id}))

    project.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert project.status == Project.Status.ARCHIVED


@pytest.mark.django_db
def test_restore_project(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Engineering")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Project", status=Project.Status.ARCHIVED)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("project-restore", kwargs={"project_id": project.id}))

    project.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert project.status == Project.Status.ACTIVE


@pytest.mark.django_db
def test_archived_project_is_read_only(api_client):
    user = User.objects.create_user(email="admin@h.com", password="pw")
    team = Team.objects.create(name="Engineering")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
    project = Project.objects.create(team=team, name="Old Project", status=Project.Status.ARCHIVED)
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse("task-create-list", kwargs={"project_id": project.id}), {"title": "Impossible Task"})

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "archived project" in response.data["detail"].lower()

    response = api_client.patch(reverse("project-detail", kwargs={"project_id": project.id}), {"name": "New Project"})

    project.refresh_from_db()
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "archived projects" in response.data["detail"].lower()
    assert project.name == "Old Project"


@pytest.mark.django_db
class TestProjectLifecycleHarden:
    def test_admin_cannot_manage_other_team_project(self, api_client):
        admin_a = User.objects.create_user(email="a@h.com", password="pw")
        team_a = Team.objects.create(name="Team A", description="A")
        TeamMembership.objects.create(user=admin_a, team=team_a, role=TeamMembership.Role.ADMIN)

        team_b = Team.objects.create(name="Team B", description="B")
        project_b = Project.objects.create(team=team_b, name="Secret B")

        api_client.force_authenticate(user=admin_a)
        response = api_client.post(reverse("project-archive", kwargs={"project_id": project_b.id}))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        project_b.refresh_from_db()
        assert project_b.status == Project.Status.ACTIVE

    def test_member_cannot_archive_project(self, api_client):
        user = User.objects.create_user(email="mem@h.com", password="pw")
        team = Team.objects.create(name="Devs")
        TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
        project = Project.objects.create(team=team, name="P1")

        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("project-archive", kwargs={"project_id": project.id}))

        assert response.status_code == status.HTTP_403_FORBIDDEN