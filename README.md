# TaskHive - Collaborative Project Management API

TaskHive is a production-style Django REST backend for team-based project and task management. It is built as an enhanced modular monolith: domain apps stay independent, business rules live in service layers, and operational concerns such as caching, background jobs, WebSockets, object storage, observability, and load testing are part of the application architecture.

The API currently uses the `/api/v1/` route prefix for compatibility, but the implementation represents the current TaskHive system.

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-6.0-green.svg)](https://www.djangoproject.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Core Capabilities

- Email/password authentication with SimpleJWT access tokens and HttpOnly refresh cookies.
- Google and GitHub social login through verified provider email addresses.
- Redis-backed access-token revocation, throttling, idempotency caching, and Channels layer.
- Team-based RBAC with `OWNER`, `ADMIN`, `MANAGER`, `MEMBER`, and `VIEWER` roles.
- Projects, tasks, subtasks, tags, comments, notifications, and attachments.
- Soft deletion for core domain records, with audit-friendly recovery managers.
- Celery workers for asynchronous notifications and project task-cascade work.
- Historical audit records for projects and tasks using `django-simple-history`.
- Team-scoped WebSocket rooms for real-time task, comment, and notification events.
- S3-compatible attachment storage with local MinIO support.
- Prometheus metrics, Grafana dashboards, and Locust load-test scripts.

## Technical Stack

- **Runtime:** Python 3.14
- **Framework:** Django 5.2 LTS, Django REST Framework
- **Authentication:** SimpleJWT, django-allauth provider identity storage
- **Database:** PostgreSQL
- **Cache/Broker:** Redis
- **Async:** Celery
- **Realtime:** Django Channels, channels-redis, Daphne
- **Object Storage:** django-storages, boto3, MinIO/S3-compatible backends
- **Observability:** django-prometheus, Prometheus, Grafana
- **Performance Testing:** Locust
- **Testing:** pytest, pytest-django, pytest-asyncio
- **API Schema:** drf-spectacular
- **Deployment:** Docker Compose

## Architecture

TaskHive is organized by domain app:

```text
task_hive/
  users/          authentication and social login
  teams/          teams, memberships, invitations, RBAC
  projects/       project lifecycle and history
  tasks/          tasks, subtasks, tags, task attachments
  comments/       comments and comment attachments
  notifications/  notification records and async tasks
  realtime/       WebSocket auth, consumers, event publishing
  common/         API contract, soft delete, permissions, middleware
  observability/  Prometheus and Grafana configuration
  performance/    Locust load-test scripts
```

Views handle HTTP parsing and serialization. Domain decisions belong in `services.py` modules. Shared policy helpers live in `common.permissions`, and shared infrastructure such as soft deletion, idempotency, and response formatting lives in `common`.

## API Contract

Current API behavior is documented in:

```text
docs/api-contract-current.md
```

Important conventions:

- Successful JSON responses use a JSend-style envelope.
- Errors use RFC 7807-style Problem Details.
- Mutating endpoints may use `Idempotency-Key` for replay-safe retries.
- WebSockets connect through `ws://<host>/ws/teams/<team_id>/?token=<access_token>`.
- Metrics are exposed at `/metrics`.

Historical V1 docs are kept in `docs/api-contract-v1.md` and `docs/openapi-v1.yaml`.

## Local Development

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run migrations and tests:

```powershell
python manage.py migrate
python manage.py check
pytest
```

Run the local Django development server:

```powershell
python manage.py runserver
```

## Docker Environment

Create a Docker environment file:

```powershell
Copy-Item .env.docker.example .env.docker
```

Use a local Docker secret without `$` characters to avoid Docker Compose interpolation warnings:

```env
SECRET_KEY=local-docker-development-secret-change-me-123456789
```

Start the production-like local stack:

```powershell
docker compose --env-file .env.docker up --build
```

Services:

- Django/Daphne API: `http://127.0.0.1:8000`
- MinIO console: `http://127.0.0.1:9001`
- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3001`

Docker uses `.env.docker`. Local Python commands use `.env`. Docker-only hostnames such as `db`, `redis`, and `minio` should not be used in local `.env`.

## Verification

Run the standard checks before release:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

Check Docker health:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health/"
Invoke-WebRequest -Uri "http://127.0.0.1:8000/metrics"
```

Run a smoke load test:

```powershell
New-Item -ItemType Directory -Force -Path "performance\reports"
locust -f performance\locustfile.py --host http://127.0.0.1:8000 --headless -u 5 -r 1 -t 1m --csv performance\reports\smoke
```
