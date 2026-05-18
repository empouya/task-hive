import pytest
from django.contrib.auth import get_user_model

from projects.models import Project
from projects.tasks import soft_delete_project_tasks
from tasks.models import Task
from teams.models import Team

User = get_user_model()


@pytest.mark.django_db
def test_soft_delete_project_tasks_marks_tasks_deleted(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True

    user = User.objects.create_user(email="cascade@h.com")
    team = Team.objects.create(name="Cascade Team")
    project = Project.objects.create(team=team, name="P1")
    Task.objects.create(project=project, creator=user, title="Task 1")
    Task.objects.create(project=project, creator=user, title="Task 2")

    deleted_count = soft_delete_project_tasks.delay(project.id, user.id).get()

    assert deleted_count == 2
    assert Task.objects.filter(project=project).count() == 0
    assert Task.all_objects.filter(project=project, is_deleted=True).count() == 2