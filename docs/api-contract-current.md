# TaskHive Current API Contract

This document describes the current TaskHive backend contract. The public HTTP API is still mounted under `/api/v1/` for compatibility, but the behavior described here represents the current system.

## Base URLs

```text
HTTP API:        /api/v1/
Health check:    /health/
Metrics:         /metrics
WebSockets:      /ws/teams/<team_id>/?token=<access_token>
```

## Authentication

TaskHive supports local email/password authentication and social login.

### Local Auth

```text
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/token/refresh/
GET  /api/v1/auth/me/
```

`login` returns a JWT access token in the JSON body and sets the refresh token as an HttpOnly cookie named `refresh_token`.

Authenticated HTTP requests use:

```text
Authorization: Bearer <access_token>
```

Logout revokes the active access token through the Redis-backed blocklist and blacklists the refresh token when present.

### Social Auth

```text
POST /api/v1/auth/social/google/
POST /api/v1/auth/social/github/
```

Request body:

```json
{
  "access_token": "provider-access-token"
}
```

The backend validates the provider token, requires a verified email address, links by email when a local user already exists, stores provider identity through django-allauth social accounts, and issues the same JWT/cookie pair as local login.

## Response Format

Successful JSON responses use a JSend-style success envelope:

```json
{
  "status": "success",
  "data": {
    "id": 1
  }
}
```

`204 No Content` responses do not include a response body.

Every response includes:

```text
X-Trace-ID: req-...
```

Clients may provide `X-Trace-ID`; otherwise the backend generates one.

## Error Format

Errors use RFC 7807-style Problem Details:

```json
{
  "type": "https://taskhive.com/errors/validation-error",
  "title": "Invalid Request Parameters",
  "status": 400,
  "detail": "One or more request parameters failed validation.",
  "instance": "/api/v1/projects/1/tasks/",
  "invalid_params": [
    {
      "name": "title",
      "reason": "This field is required."
    }
  ],
  "trace_id": "req-..."
}
```

Common error categories:

```text
validation-error
permission_denied
not_authenticated
not_found
business_logic_violation
idempotency-conflict
server-error
```

## Idempotency

Mutable endpoints support optional idempotency keys:

```text
Idempotency-Key: <client-generated-uuid>
```

Supported methods:

```text
POST
PUT
PATCH
```

Behavior:

- Same user, method, path, key, and request body replays the cached response.
- Same user, method, path, and key with a different body returns `409`.
- Cached idempotency responses expire after 24 hours.

## Rate Limiting

DRF throttling is enabled with Redis-backed cache storage when Redis is configured.

Default rates:

```text
Anonymous:      60/min
Authenticated: 1000/min
```

## Teams And RBAC

Roles:

```text
OWNER
ADMIN
MANAGER
MEMBER
VIEWER
```

General policy:

- `OWNER` and `ADMIN` can manage teams, invitations, and members.
- `MANAGER` can manage projects and moderate workspace content.
- `MEMBER` can create and update tasks/comments in their teams.
- `VIEWER` is read-only.

Team endpoints:

```text
GET    /api/v1/teams/
POST   /api/v1/teams/
PATCH  /api/v1/teams/<team_id>/
DELETE /api/v1/teams/<team_id>/
GET    /api/v1/teams/<team_id>/members/
DELETE /api/v1/teams/<team_id>/members/<user_id>/
POST   /api/v1/teams/<team_id>/invites/
GET    /api/v1/teams/<team_id>/invites/
DELETE /api/v1/teams/<team_id>/invites/<invite_id>/
POST   /api/v1/invites/<token>/accept/
```

Newly created teams assign the creator as `OWNER`.

## Projects

Project endpoints:

```text
GET   /api/v1/teams/<team_id>/projects/
POST  /api/v1/teams/<team_id>/projects/
PATCH /api/v1/projects/<project_id>/
POST  /api/v1/projects/<project_id>/archive/
POST  /api/v1/projects/<project_id>/restore/
```

Projects are scoped to teams. Archived projects are read-only for project/task/comment mutations except explicit restore.

Projects use soft deletion internally and are audited with historical records.

## Tasks, Subtasks, And Tags

Task endpoints:

```text
GET    /api/v1/projects/<project_id>/tasks/
POST   /api/v1/projects/<project_id>/tasks/
PATCH  /api/v1/tasks/<task_id>/
DELETE /api/v1/tasks/<task_id>/
PATCH  /api/v1/tasks/<task_id>/assign/
PATCH  /api/v1/tasks/<task_id>/reorder/
```

Tasks support:

- status: `TODO`, `IN_PROGRESS`, `DONE`
- priority: `LOW`, `MEDIUM`, `HIGH`
- assignee
- decimal board position
- optional parent task for subtasks
- project-scoped tags

Tasks use soft deletion and are audited with historical records.

## Comments

Comment endpoints:

```text
GET    /api/v1/tasks/<task_id>/comments/
POST   /api/v1/tasks/<task_id>/comments/
DELETE /api/v1/comments/<comment_id>/
```

Comments are team-visible through their parent task and project. Comments use soft deletion.

## Notifications

Notification endpoints:

```text
GET   /api/v1/notifications/
PATCH /api/v1/notifications/<notification_id>/read/
```

Notifications are created asynchronously for task assignment and comment events.

## Attachments

Task and comment attachment domain models are available in the backend and use S3-compatible storage through `django-storages`.

Current storage behavior:

- Local non-Docker development defaults to filesystem storage.
- Docker uses MinIO through S3-compatible settings.
- Production can use AWS S3 or compatible services such as Cloudflare R2 by changing environment variables.

Public upload endpoints are not exposed yet; attachment creation currently lives behind service functions.

## Realtime WebSockets

Team-scoped WebSocket endpoint:

```text
ws://<host>/ws/teams/<team_id>/?token=<access_token>
```

The token must be a valid JWT access token and must not be revoked.

On successful connection:

```json
{
  "type": "connection.accepted",
  "team_id": 1
}
```

Client ping:

```json
{
  "type": "ping"
}
```

Server pong:

```json
{
  "type": "pong"
}
```

Published event types include:

```text
task.created
task.updated
task.deleted
task.reordered
task.assigned
comment.created
comment.deleted
notification.created
```

Payloads are intentionally lightweight and ID-driven so clients can refetch full resources when needed.

## Observability

Metrics endpoint:

```text
GET /metrics
```

Prometheus scrapes Django metrics every 15 seconds in Docker. Grafana is provisioned with a Prometheus data source and a starter TaskHive dashboard.

Docker service URLs:

```text
API:        http://127.0.0.1:8000
Prometheus: http://127.0.0.1:9090
Grafana:    http://127.0.0.1:3001
MinIO:      http://127.0.0.1:9001
```

## Performance Testing

Locust scripts live in:

```text
performance/locustfile.py
```

Smoke profile:

```powershell
locust -f performance/locustfile.py --host http://127.0.0.1:8000 --headless -u 5 -r 1 -t 1m --csv performance\reports\smoke
```

Target indicators for local smoke/load tests:

- 0% 5xx responses.
- p95 list endpoint latency near or below 150ms in local Docker where practical.
- Stable Prometheus scrape target during test execution.
