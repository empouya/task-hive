import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from common.permissions import can_read_team
from teams.models import Team


class TeamConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.team_id = self.scope["url_route"]["kwargs"]["team_id"]
        self.group_name = f"team.{self.team_id}"
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        has_access = await self._can_access_team(user.id, self.team_id)
        if not has_access:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            "type": "connection.accepted",
            "team_id": self.team_id,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def team_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def _can_access_team(self, user_id, team_id):
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return False

        user = self.scope["user"]
        return can_read_team(user, team)