import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from comments.attachments import create_comment_attachment, delete_comment_attachment
from comments.models import Comment, CommentAttachment
from common.exceptions import PermissionDeniedError
from projects.models import Project
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_member_can_create_comment_attachment(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        }
    }
    user = User.objects.create_user(email="attach-comment@h.com", password="pw")
    team = Team.objects.create(name="Comment Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    comment = Comment.objects.create(task=task, author=user, content="Comment")
    uploaded_file = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")

    attachment = create_comment_attachment(user=user, comment_id=comment.id, file=uploaded_file)

    assert attachment.team == team
    assert attachment.comment == comment
    assert attachment.uploaded_by == user
    assert attachment.original_filename == "note.txt"
    assert attachment.content_type == "text/plain"
    assert attachment.size == 5


@pytest.mark.django_db
def test_viewer_cannot_create_comment_attachment():
    user = User.objects.create_user(email="viewer-attach-comment@h.com", password="pw")
    team = Team.objects.create(name="Viewer Comment Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.VIEWER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    comment = Comment.objects.create(task=task, author=user, content="Comment")
    uploaded_file = SimpleUploadedFile("note.txt", b"hello", content_type="text/plain")

    with pytest.raises(PermissionDeniedError):
        create_comment_attachment(user=user, comment_id=comment.id, file=uploaded_file)


@pytest.mark.django_db
def test_comment_attachment_soft_delete(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.InMemoryStorage",
        }
    }

    user = User.objects.create_user(email="delete-comment-attachment@h.com", password="pw")
    team = Team.objects.create(name="Delete Comment Attachment Team")
    TeamMembership.objects.create(user=user, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=user, title="Task")
    comment = Comment.objects.create(task=task, author=user, content="Comment")
    attachment = create_comment_attachment(
        user=user,
        comment_id=comment.id,
        file=SimpleUploadedFile("note.txt", b"hello", content_type="text/plain"),
    )

    delete_comment_attachment(user=user, attachment_id=attachment.id)

    assert not CommentAttachment.objects.filter(id=attachment.id).exists()
    assert CommentAttachment.all_objects.filter(id=attachment.id, is_deleted=True).exists()