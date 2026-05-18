from celery import shared_task
from django.contrib.auth import get_user_model

from projects.models import Project
from tasks.models import Task

User = get_user_model()


@shared_task
def soft_delete_project_tasks(project_id, deleted_by_id=None):
    deleted_by = None

    if deleted_by_id:
        deleted_by = User.objects.filter(id=deleted_by_id).first()

    try:
        project = Project.all_objects.get(id=project_id)
    except Project.DoesNotExist:
        return 0

    deleted_count = 0
    for task in Task.objects.filter(project=project).iterator():
        task.soft_delete(deleted_by=deleted_by)
        deleted_count += 1

    return deleted_count