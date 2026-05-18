from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from users.authentication import RedisBlocklistJWTAuthentication


@database_sync_to_async
def get_user_for_token(raw_token):
    authenticator = RedisBlocklistJWTAuthentication()

    try:
        validated_token = authenticator.get_validated_token(raw_token)
        return authenticator.get_user(validated_token)
    except (InvalidToken, TokenError):
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Authenticate WebSockets with ?token=<access-token>.

    This mirrors DRF JWT auth and checks the Redis-backed token blocklist.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_params = parse_qs(scope.get("query_string", b"").decode())
        token = query_params.get("token", [None])[0]

        scope["user"] = AnonymousUser()
        if token:
            scope["user"] = await get_user_for_token(token)

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)