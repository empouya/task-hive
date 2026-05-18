from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings

from common.cache_keys import jwt_blocklist_key


class RedisBlocklistJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)
        jti = validated_token.get(api_settings.JTI_CLAIM)

        if jti and cache.get(jwt_blocklist_key(jti)):
            raise InvalidToken("Token has been revoked.")

        return validated_token