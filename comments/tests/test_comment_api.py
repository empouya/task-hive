import pytest
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status

from comments.models import Comment
from projects.models import Project
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_create_comment(api_client):
    user1 = User.objects.create_user(email="user1@h.com", password="pw")
    user2 = User.objects.create_user(email="user2@h.com", password="pw")
    team = Team.objects.create(name="Comment Team")
    TeamMembership.objects.create(user=user1, team=team, role=TeamMembership.Role.MEMBER)
    TeamMembership.objects.create(user=user2, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="Board")
    task = Task.objects.create(project=project, creator=user1, title="Task 1", position=1.0)

    api_client.force_authenticate(user=user2)
    response = api_client.post(reverse("comment-create-list", kwargs={"task_id": task.id}), {"content": "This task is so cool!"})

    assert response.status_code == status.HTTP_201_CREATED
    comment = get_object_or_404(Comment, id=response.data["id"])
    assert comment.content == "This task is so cool!"
    assert comment.task == task
    assert comment.author == user2


@pytest.mark.django_db
def test_delete_comment_soft_deletes(api_client):
    admin = User.objects.create_user(email="a@h.com")
    member = User.objects.create_user(email="m@h.com")
    team = Team.objects.create(name="Mod Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, title="Task")
    comment = Comment.objects.create(task=task, author=member, content="Delete me if you can!")
    url = reverse("comment-detail", kwargs={"comment_id": comment.id})

    api_client.force_authenticate(user=member)
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Comment.objects.filter(id=comment.id).exists()

    api_client.force_authenticate(user=admin)
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Comment.objects.filter(id=comment.id).exists()
    assert Comment.all_objects.filter(id=comment.id, is_deleted=True).exists()


@pytest.mark.django_db
class TestCommentSecurityHarden:
    def test_cannot_comment_on_other_team_task(self, api_client):
        owner = User.objects.create_user(email="owner@h.com", password="pw")
        stranger = User.objects.create_user(email="stranger@h.com", password="pw")
        team = Team.objects.create(name="Private Team")
        TeamMembership.objects.create(user=owner, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="Secret")
        task = Task.objects.create(project=project, creator=owner, title="Task")

        api_client.force_authenticate(user=stranger)
        response = api_client.post(reverse("comment-create-list", kwargs={"task_id": task.id}), {"content": "I shouldn't be here"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_comment_on_archived_project_task(self, api_client):
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
        project = Project.objects.create(team=team, name="Old", status=Project.Status.ARCHIVED)
        task = Task.objects.create(project=project, creator=user, title="Frozen Task")

        api_client.force_authenticate(user=user)
        response = api_client.post(reverse("comment-create-list", kwargs={"task_id": task.id}), {"content": "Attempting to comment"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_comments_remain_as_soft_deleted_task_history(self, api_client):
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="P1")
        task = Task.objects.create(project=project, creator=user, title="Task")
        comment = Comment.objects.create(task=task, author=user, content="Permanent record?")

        task.soft_delete(deleted_by=user)

        assert not Task.objects.filter(id=task.id).exists()
        assert Task.all_objects.filter(id=task.id, is_deleted=True).exists()
        assert Comment.objects.filter(id=comment.id).exists()

    def test_comment_update_is_not_allowed(self, api_client):
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.ADMIN)
        project = Project.objects.create(team=team, name="P1")
        task = Task.objects.create(project=project, creator=user, title="Task")
        comment = Comment.objects.create(task=task, author=user, content="Original")

        api_client.force_authenticate(user=user)
        response = api_client.patch(reverse("comment-detail", kwargs={"comment_id": comment.id}), {"content": "Hacker Edit"})

        assert response.status_code in [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]