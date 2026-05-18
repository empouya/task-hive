JWT_BLOCKLIST_PREFIX = "jwt:blocklist"
IDEMPOTENCY_PREFIX = "idempotency"


def jwt_blocklist_key(jti):
    return f"{JWT_BLOCKLIST_PREFIX}:{jti}"


def idempotency_key(user_id, method, path, key):
    return f"{IDEMPOTENCY_PREFIX}:{user_id}:{method}:{path}:{key}"