from django.shortcuts import get_object_or_404

from comments.models import Comment, CommentAttachment
from common.exceptions import PermissionDeniedError
from common.permissions import can_comment, can_read_team


def create_comment_attachment(*, user, comment_id, file):
    comment = get_object_or_404(Comment.objects.select_related("task__project__team"), id=comment_id)
    team = comment.task.project.team

    if not can_comment(user, team):
        raise PermissionDeniedError("You do not have permission to attach files to this comment.")

    return CommentAttachment.objects.create(
        team=team,
        comment=comment,
        uploaded_by=user,
        file=file,
        original_filename=file.name,
        content_type=getattr(file, "content_type", ""),
        size=file.size,
    )


def list_comment_attachments(*, user, comment_id):
    comment = get_object_or_404(Comment.objects.select_related("task__project__team"), id=comment_id)

    if not can_read_team(user, comment.task.project.team):
        raise PermissionDeniedError("You do not have access to this comment.")

    return comment.attachments.select_related("uploaded_by").order_by("-created_at")


def delete_comment_attachment(*, user, attachment_id):
    attachment = get_object_or_404(
        CommentAttachment.objects.select_related("comment__task__project__team"),
        id=attachment_id,
    )

    if not can_comment(user, attachment.comment.task.project.team):
        raise PermissionDeniedError("You do not have permission to delete this attachment.")

    attachment.soft_delete(deleted_by=user)
    return attachment