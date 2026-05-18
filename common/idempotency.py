import hashlib
import json

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

from common.cache_keys import idempotency_key

IDEMPOTENCY_HEADER = "HTTP_IDEMPOTENCY_KEY"
IDEMPOTENCY_RESPONSE_HEADER = "Idempotency-Replayed"
MUTATION_METHODS = {"POST", "PUT", "PATCH"}
CACHE_TIMEOUT_SECONDS = 60 * 60 * 24


class IdempotencyMiddleware:
    """
    Cache mutation responses by user, method, path, idempotency key, and body hash.

    Reusing the same key with the same body replays the cached response.
    Reusing the same key with a different body returns 409.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        idempotency_key_value = request.META.get(IDEMPOTENCY_HEADER)

        if request.method not in MUTATION_METHODS or not idempotency_key_value:
            return self.get_response(request)

        user_id = "anonymous"
        if getattr(request, "user", None) and request.user.is_authenticated:
            user_id = request.user.id

        body_hash = hashlib.sha256(request.body or b"").hexdigest()
        cache_key = idempotency_key(
            user_id=user_id,
            method=request.method,
            path=request.path,
            key=idempotency_key_value,
        )

        cached = cache.get(cache_key)
        if cached:
            if cached["body_hash"] != body_hash:
                return _idempotency_conflict_response(request)

            response = HttpResponse(
                cached["content"],
                status=cached["status_code"],
                content_type=cached["content_type"],
            )
            response[IDEMPOTENCY_RESPONSE_HEADER] = "true"
            return response

        response = self.get_response(request)

        if response.status_code < 500:
            if hasattr(response, "render") and not response.is_rendered:
                response.render()

            cache.set(
                cache_key,
                {
                    "body_hash": body_hash,
                    "status_code": response.status_code,
                    "content_type": response.get("Content-Type", "application/json"),
                    "content": bytes(response.content),
                },
                timeout=CACHE_TIMEOUT_SECONDS,
            )

        response[IDEMPOTENCY_RESPONSE_HEADER] = "false"
        return response


def _idempotency_conflict_response(request):
    trace_id = getattr(request, "trace_id", None)

    payload = {
        "type": "https://taskhive.com/errors/idempotency-conflict",
        "title": "Idempotency Key Conflict",
        "status": 409,
        "detail": "This Idempotency-Key was already used with a different request body.",
        "instance": request.path,
    }

    if trace_id:
        payload["trace_id"] = trace_id

    return JsonResponse(payload, status=409)