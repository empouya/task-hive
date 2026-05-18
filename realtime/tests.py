import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from task_hive.asgi import application
from teams.models import Team, TeamMembership

User = get_user_model()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_team_websocket_accepts_team_member(settings):
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

    user = await sync_to_async(User.objects.create_user)(email="ws-member@h.com", password="pw")
    team = await sync_to_async(Team.objects.create)(name="Realtime Team")
    await sync_to_async(TeamMembership.objects.create)(
        user=user,
        team=team,
        role=TeamMembership.Role.MEMBER,
    )
    token = await sync_to_async(lambda: str(RefreshToken.for_user(user).access_token))()

    communicator = WebsocketCommunicator(application, f"/ws/teams/{team.id}/?token={token}")
    connected, _ = await communicator.connect()

    assert connected is True
    response = await communicator.receive_json_from()
    assert response["type"] == "connection.accepted"

    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_team_websocket_rejects_non_member(settings):
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }

    user = await sync_to_async(User.objects.create_user)(email="ws-stranger@h.com", password="pw")
    team = await sync_to_async(Team.objects.create)(name="Private Realtime Team")
    token = await sync_to_async(lambda: str(RefreshToken.for_user(user).access_token))()

    communicator = WebsocketCommunicator(application, f"/ws/teams/{team.id}/?token={token}")
    connected, _ = await communicator.connect()

    assert connected is False