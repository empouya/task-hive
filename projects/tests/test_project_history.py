import pytest

from projects.models import Project
from teams.models import Team


@pytest.mark.django_db
def test_project_history_records_create_and_update():
    team = Team.objects.create(name="History Team")
    project = Project.objects.create(team=team, name="Original")

    project.name = "Updated"
    project.save(update_fields=["name"])

    assert project.history.count() == 2
    assert project.history.first().name == "Updated"