from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404

from common.exceptions import BusinessLogicError, PermissionDeniedError
from common.permissions import can_manage_projects, can_read_team, can_reorder_tasks, can_write_tasks
from projects.models import Project
from tasks.models import Tag, Task
from teams.models import TeamMembership


def get_object_or_404_project(project_id):
    return get_object_or_404(Project.objects.select_related("team"), id=project_id)


def list_tasks(*, user, project_id):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_read_team(user, project.team):
        raise PermissionDeniedError("You do not have access to this project's tasks.")

    return (
        project.tasks
        .select_related("project", "creator", "assignee", "parent")
        .prefetch_related("tags")
        .order_by("position")
    )


@transaction.atomic
def create_task(*, user, project_id, data):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)
    team = project.team

    if not can_write_tasks(user, team):
        raise PermissionDeniedError("You are not a member of this team.")

    if project.status == Project.Status.ARCHIVED:
        raise BusinessLogicError("Cannot create tasks in an archived project.")

    assignee = data.get("assignee")
    if assignee and not TeamMembership.objects.filter(user=assignee, team=team).exists():
        raise BusinessLogicError("Assignee must be a member of the team.")

    parent = data.get("parent")
    if parent and parent.project_id != project.id:
        raise BusinessLogicError("Parent task must belong to the same project.")

    tags = data.pop("tags", [])
    max_position = project.tasks.aggregate(max_position=Max("position"))["max_position"] or Decimal("0")
    task = Task.objects.create(
        project=project,
        creator=user,
        position=max_position + Decimal("1.0"),
        **data,
    )
    task.tags.set(tags)
    return task


@transaction.atomic
def update_task(*, user, task_id, serializer_class, data):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if not can_write_tasks(user, task.project.team):
        raise PermissionDeniedError("Access denied.")

    if task.project.status == Project.Status.ARCHIVED:
        raise PermissionDeniedError("Project is archived.")

    serializer = serializer_class(task, data=data, partial=True)
    serializer.is_valid(raise_exception=True)

    parent = serializer.validated_data.get("parent")
    if parent and parent.project_id != task.project_id:
        raise BusinessLogicError("Parent task must belong to the same project.")

    return serializer.save()


@transaction.atomic
def delete_task(*, user, task_id):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if not can_write_tasks(user, task.project.team):
        raise PermissionDeniedError("Access denied.")

    if task.project.status == Project.Status.ARCHIVED:
        raise PermissionDeniedError("Project is archived.")

    task.soft_delete(deleted_by=user)
    return task


@transaction.atomic
def reorder_task(*, user, task_id, target_position):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if task.project.status == Project.Status.ARCHIVED:
        raise PermissionDeniedError("Project is archived.")

    if not can_reorder_tasks(user, task.project.team):
        raise PermissionDeniedError("Access denied.")

    if target_position is None:
        raise BusinessLogicError("Position is required.")

    task.position = Decimal(str(target_position))
    task.save(update_fields=["position", "updated_at"])
    return task


@transaction.atomic
def assign_task(*, user, task_id, assignee_id):
    task = get_object_or_404(Task.objects.select_related("project__team"), id=task_id)

    if not can_manage_projects(user, task.project.team):
        raise PermissionDeniedError("Only managers and admins can reassign tasks.")

    if assignee_id:
        if not TeamMembership.objects.filter(user_id=assignee_id, team=task.project.team).exists():
            raise BusinessLogicError("User is not in this team.")
        task.assignee_id = assignee_id
    else:
        task.assignee = None

    task.save(update_fields=["assignee", "updated_at"])
    return task


def list_tags(*, user, project_id):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_read_team(user, project.team):
        raise PermissionDeniedError("You do not have access to this project's tags.")

    return Tag.objects.filter(project=project).order_by("name")


@transaction.atomic
def create_tag(*, user, project_id, name, color=""):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_manage_projects(user, project.team):
        raise PermissionDeniedError("Only managers and admins can create tags.")

    tag, _ = Tag.objects.get_or_create(
        project=project,
        name=name,
        defaults={
            "team": project.team,
            "color": color,
        },
    )
    return tag


class TaskService:
    @staticmethod
    def reorder_task(task, target_position):
        task.position = Decimal(str(target_position))
        task.save(update_fields=["position", "updated_at"])
        return task