import pytest
from django.contrib.auth import get_user_model

from comments.models import Comment
from notifications.models import Notification
from projects.models import Project
from tasks.models import Task
from teams.models import Team

User = get_user_model()


@pytest.mark.django_db
def test_comment_notification_task_creates_notification(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    author = User.objects.create_user(email="author@h.com")
    assignee = User.objects.create_user(email="assignee@h.com")
    team = Team.objects.create(name="Async Notify Team")
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=author, assignee=assignee, title="Task")
    Comment.objects.create(task=task, author=author, content="Heads up")

    assert Notification.objects.filter(
        recipient=assignee,
        actor=author,
        verb="commented on",
        target_task=task,
    ).exists()


@pytest.mark.django_db
def test_assignment_notification_task_creates_notification(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    creator = User.objects.create_user(email="creator@h.com")
    assignee = User.objects.create_user(email="assigned@h.com")
    team = Team.objects.create(name="Async Assignment Team")
    project = Project.objects.create(team=team, name="P1")

    task = Task.objects.create(
        project=project,
        creator=creator,
        assignee=assignee,
        title="Assigned Task",
    )

    assert Notification.objects.filter(
        recipient=assignee,
        actor=creator,
        verb="assigned you to",
        target_task=task,
    ).exists()