from django.urls import path

from realtime.consumers import TeamConsumer

websocket_urlpatterns = [
    path("ws/teams/<int:team_id>/", TeamConsumer.as_asgi()),
]