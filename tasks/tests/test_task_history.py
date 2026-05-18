import pytest
from django.contrib.auth import get_user_model

from projects.models import Project
from tasks.models import Task
from teams.models import Team

User = get_user_model()


@pytest.mark.django_db
def test_task_history_records_create_and_update():
    user = User.objects.create_user(email="history-task@h.com")
    team = Team.objects.create(name="Task History Team")
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Original")

    task.title = "Updated"
    task.save(update_fields=["title"])

    assert task.history.count() == 2
    assert task.history.first().title == "Updated"