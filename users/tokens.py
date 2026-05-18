import time

from django.core.cache import cache
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.cache_keys import jwt_blocklist_key


def revoke_access_token(raw_token):
    token = AccessToken(raw_token)
    jti = token[api_settings.JTI_CLAIM]
    exp = int(token["exp"])
    ttl = max(exp - int(time.time()), 0)

    if ttl > 0:
        cache.set(jwt_blocklist_key(jti), True, timeout=ttl)

    return jti


def revoke_refresh_token(raw_token):
    token = RefreshToken(raw_token)
    token.blacklist()
    return token