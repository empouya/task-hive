from django.shortcuts import get_object_or_404

from common.exceptions import BusinessLogicError, PermissionDeniedError
from common.permissions import can_manage_projects, can_read_team
from projects.models import Project
from teams.models import Team


def create_project(*, user, team_id, data):
    team = get_object_or_404(Team, id=team_id)

    if not can_manage_projects(user, team):
        raise PermissionDeniedError("Only team managers and admins can create projects.")

    return Project.objects.create(team=team, **data)


def list_projects(*, user, team_id):
    team = get_object_or_404(Team, id=team_id)

    if not can_read_team(user, team):
        raise PermissionDeniedError("You do not have access to this team's projects.")

    return (
        team.projects
        .filter(status=Project.Status.ACTIVE)
        .select_related("team")
        .order_by("created_at")
    )


def update_project(*, user, project_id, serializer_class, data):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_manage_projects(user, project.team):
        raise PermissionDeniedError("Admin rights required for this team.")

    if project.status == Project.Status.ARCHIVED:
        raise PermissionDeniedError("Archived projects cannot be modified.")

    if "status" in data:
        raise BusinessLogicError("You're not allowed to change the status of this project!")

    serializer = serializer_class(project, data=data, partial=True)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def archive_project(*, user, project_id):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_manage_projects(user, project.team):
        raise PermissionDeniedError("Admin rights required for this team.")

    project.status = Project.Status.ARCHIVED
    project.save(update_fields=["status"])
    return project


def restore_project(*, user, project_id):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_manage_projects(user, project.team):
        raise PermissionDeniedError("Admin rights required for this team.")

    project.status = Project.Status.ACTIVE
    project.save(update_fields=["status"])
    return project


def soft_delete_project(*, user, project_id):
    project = get_object_or_404(Project.objects.select_related("team"), id=project_id)

    if not can_manage_projects(user, project.team):
        raise PermissionDeniedError("Admin rights required for this team.")

    project.soft_delete(deleted_by=user)
    return project