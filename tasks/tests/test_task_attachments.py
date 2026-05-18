import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from common.exceptions import PermissionDeniedError
from projects.models import Project
from tasks.attachments import create_task_attachment, delete_task_attachment, list_task_attachments
from tasks.models import Task, TaskAttachment
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_member_can_create_task_attachment(settings):
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

    user = User.objects.create_user(email="attach-task@h.com", password="pw")
    team = Team.objects.create(name="Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    uploaded_file = SimpleUploadedFile("spec.txt", b"hello", content_type="text/plain")

    attachment = create_task_attachment(user=user, task_id=task.id, file=uploaded_file)

    assert attachment.team == team
    assert attachment.task == task
    assert attachment.uploaded_by == user
    assert attachment.original_filename == "spec.txt"
    assert attachment.content_type == "text/plain"
    assert attachment.size == 5


@pytest.mark.django_db
def test_viewer_cannot_create_task_attachment():
    user = User.objects.create_user(email="viewer-attach-task@h.com", password="pw")
    team = Team.objects.create(name="Viewer Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.VIEWER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    uploaded_file = SimpleUploadedFile("spec.txt", b"hello", content_type="text/plain")

    with pytest.raises(PermissionDeniedError):
        create_task_attachment(user=user, task_id=task.id, file=uploaded_file)


@pytest.mark.django_db
def test_task_attachment_soft_delete(settings):
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

    user = User.objects.create_user(email="delete-task-attachment@h.com", password="pw")
    team = Team.objects.create(name="Delete Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    attachment = create_task_attachment(
        user=user,
        task_id=task.id,
        file=SimpleUploadedFile("spec.txt", b"hello", content_type="text/plain"),
    )

    delete_task_attachment(user=user, attachment_id=attachment.id)

    assert not TaskAttachment.objects.filter(id=attachment.id).exists()
    assert TaskAttachment.all_objects.filter(id=attachment.id, is_deleted=True).exists()


@pytest.mark.django_db
def test_task_attachment_list_requires_team_access(settings):
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

    owner = User.objects.create_user(email="owner-task-attachment@h.com", password="pw")
    stranger = User.objects.create_user(email="stranger-task-attachment@h.com", password="pw")
    team = Team.objects.create(name="Private Attachment Team")
    TeamMembership.objects.create(user=owner, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=owner, title="Task")
    create_task_attachment(
        user=owner,
        task_id=task.id,
        file=SimpleUploadedFile("spec.txt", b"hello", content_type="text/plain"),
    )

    with pytest.raises(PermissionDeniedError):
        list_task_attachments(user=stranger, task_id=task.id)