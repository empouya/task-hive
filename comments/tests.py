import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from teams.models import TeamMembership, Team
from projects.models import Project
from .models import Comment
from tasks.models import Task
User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_task_reordering_logic(api_client):
    # Setup
    user1 = User.objects.create_user(email="user1@h.com", password="pw")
    user2 = User.objects.create_user(email="user2@h.com", password="pw")
    team = Team.objects.create(name="Comment Team")
    TeamMembership.objects.create(user=user1, team=team)
    TeamMembership.objects.create(user=user2, team=team)
    project = Project.objects.create(team=team, name="Board")
    
    task1 = Task.objects.create(project=project, creator=user1, title="Task 1", position=1.0)
    task2 = Task.objects.create(project=project, creator=user2, title="Task 2", position=2.0)
    
    api_client.force_authenticate(user=user2)
    
    url = reverse('comment-create-list', kwargs={'task_id': task1.id})
    response = api_client.post(url, {"content": "This task is so cool!"})
    assert response.status_code == 201
    
    comment = get_object_or_404(Comment, id=response.data['id'])
    assert comment.content == "This task is so cool!"
    assert comment.task_id == 1
    assert comment.author_id == 2

@pytest.mark.django_db
def test_delete_comment(api_client):
    # Setup
    admin = User.objects.create_user(email="a@h.com")
    member = User.objects.create_user(email="m@h.com")
    team = Team.objects.create(name="Mod Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, title="Task")
    comment = Comment.objects.create(task=task, author=member, content="Delete me if you can!")
    url = reverse('comment-detail', kwargs={'comment_id': comment.id})

    # API call (Member)
    api_client.force_authenticate(user=member)
    response = api_client.delete(url)

    # Test (Member)
    assert response.status_code == 403
    assert Comment.objects.filter(id=comment.id).exists()

    #  API call (Admin)
    api_client.force_authenticate(user=admin)
    response = api_client.delete(url)

    # Test (Admin)
    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment.id).exists()

@pytest.mark.django_db
class TestCommentSecurityHarden:

    def test_cannot_comment_on_other_team_task(self, api_client):
        """Users should not be able to comment on tasks outside their team."""
        owner = User.objects.create_user(email="owner@h.com", password="pw")
        stranger = User.objects.create_user(email="stranger@h.com", password="pw")
        team = Team.objects.create(name="Private Team")
        TeamMembership.objects.create(user=owner, team=team, role='ADMIN')
        
        project = Project.objects.create(team=team, name="Secret")
        task = Task.objects.create(project=project, creator=owner, title="Task")

        api_client.force_authenticate(user=stranger)
        url = reverse('comment-create-list', kwargs={'task_id': task.id})
        response = api_client.post(url, {"content": "I shouldn't be here"})

        assert response.status_code == 403

    def test_cannot_comment_on_archived_project_task(self, api_client):
        """Tasks in archived projects should not accept new comments."""
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team)
        
        # Setup Archived Project
        project = Project.objects.create(team=team, name="Old", status=Project.Status.ARCHIVED)
        task = Task.objects.create(project=project, creator=user, title="Frozen Task")

        api_client.force_authenticate(user=user)
        url = reverse('comment-create-list', kwargs={'task_id': task.id})
        response = api_client.post(url, {"content": "Attempting to comment"})

        assert response.status_code == 403 # Or 400 depending on your check

    def test_comments_deleted_on_task_cascade(self, api_client):
        """If a task is deleted, its comments must be purged."""
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team, role='ADMIN')
        project = Project.objects.create(team=team, name="P1")
        task = Task.objects.create(project=project, creator=user, title="Task")
        Comment.objects.create(task=task, author=user, content="Permanent record?")

        # Delete Task
        task.delete()

        assert Comment.objects.filter(task_id=task.id).count() == 0

    def test_comment_update_is_not_allowed(self, api_client):
        """Ensure no PATCH/PUT endpoint exists to edit comments."""
        user = User.objects.create_user(email="u@h.com", password="pw")
        team = Team.objects.create(name="T1")
        TeamMembership.objects.create(user=user, team=team, role='ADMIN')
        project = Project.objects.create(team=team, name="P1")
        task = Task.objects.create(project=project, creator=user, title="Task")
        comment = Comment.objects.create(task=task, author=user, content="Original")

        api_client.force_authenticate(user=user)
        url = reverse('comment-detail', kwargs={'comment_id': comment.id})
        
        # Attempt to Update
        response = api_client.patch(url, {"content": "Hacker Edit"})
        
        # Should be 405 Method Not Allowed if not implemented, or 403 if restricted
        assert response.status_code in [405, 403]
