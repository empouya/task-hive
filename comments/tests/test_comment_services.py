import pytest
from django.contrib.auth import get_user_model

from comments import services
from comments.models import Comment
from projects.models import Project
from tasks.models import Task
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.django_db
def test_delete_comment_is_soft_delete():
    admin = User.objects.create_user(email="comment-admin@h.com", password="pw")
    member = User.objects.create_user(email="comment-member@h.com", password="pw")
    team = Team.objects.create(name="Comment Team")
    TeamMembership.objects.create(user=admin, team=team, role=TeamMembership.Role.ADMIN)
    TeamMembership.objects.create(user=member, team=team, role=TeamMembership.Role.MEMBER)
    project = Project.objects.create(team=team, name="P1")
    task = Task.objects.create(project=project, creator=admin, title="Task")
    comment = Comment.objects.create(task=task, author=member, content="Delete me")

    services.delete_comment(user=admin, comment_id=comment.id)

    assert not Comment.objects.filter(id=comment.id).exists()
    assert Comment.all_objects.filter(id=comment.id, is_deleted=True).exists()