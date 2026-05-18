import pytest
from django.contrib.auth import get_user_model

from teams.models import Team

User = get_user_model()


@pytest.mark.django_db
def test_soft_delete_hides_team_from_default_manager():
    team = Team.objects.create(name="Archived Team")

    team.soft_delete()

    assert not Team.objects.filter(id=team.id).exists()
    assert Team.all_objects.filter(id=team.id, is_deleted=True).exists()


@pytest.mark.django_db
def test_soft_delete_records_deletion_context():
    user = User.objects.create_user(email="deleter@taskhive.com", password="pw")
    team = Team.objects.create(name="Context Team")

    team.soft_delete(deleted_by=user)
    team.refresh_from_db()

    assert team.is_deleted is True
    assert team.deleted_at is not None
    assert team.deleted_by == user


@pytest.mark.django_db
def test_soft_deleted_team_can_be_restored():
    team = Team.objects.create(name="Restorable Team")
    team.soft_delete()

    team.restore()

    assert Team.objects.filter(id=team.id).exists()
    assert team.is_deleted is False
    assert team.deleted_at is None
    assert team.deleted_by is None