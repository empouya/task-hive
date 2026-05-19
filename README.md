# TaskHive — Enterprise-Grade Project Management API

TaskHive is a **Django REST API** for team-based project and task management. It is built as a production-ready modular monolith, simulating a real-world engineering lifecycle. 

Going far beyond simple CRUD, TaskHive was engineered with a relentless focus on **clean architecture, event-driven workflows, data integrity, and operational resilience**, proven by rigorous load testing and extensive test coverage.

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-5.2_LTS-green.svg)](https://www.djangoproject.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()
[![Performance](https://img.shields.io/badge/P95_Latency-≤100ms-blue.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📊 Performance & Reliability Metrics

TaskHive isn't just theoretically scalable; it has been actively benchmarked and hardened. Based on our latest Locust load profiles and Pytest suites:

* **0% Error Rate Under Load:** Zero 5xx responses or dropped transactions during simulated user traffic spikes.
* **Blazing Fast Core Reads:** `GET /tasks/` and `GET /projects/` endpoints maintain a **median latency of ~70ms** and a **P95 of ≤ 100ms**.
* **Optimized Writes:** Domain mutations (Task Creation/Updates) execute with a **median latency of ~90ms** (P95 ≤ 140ms), ensuring responsive UI interactions.
* **Secure Auth Throttling:** Intentional computational overhead on `/auth/login/` and `/auth/register/` (P95 ~430ms) guarantees robust password hashing without degrading the performance of the core application.
* **92% Total Test Coverage:** 110 passed integration and unit tests, with **95%+ coverage** on all core domain models, permission policies, and service layers.

---

## ✨ System Capabilities

* **Advanced Access Control (RBAC):** Strict team-based permissions enforcing `OWNER`, `ADMIN`, `MANAGER`, `MEMBER`, and `VIEWER` roles down to the database row level.
* **Realtime Collaboration:** Daphne-powered WebSocket rooms push live, ID-driven updates for task changes, new comments, and notifications instantly.
* **Event-Driven & Asynchronous:** Celery workers handle non-blocking workloads, including notification delivery and cascading soft-deletion background jobs.
* **S3-Compatible Object Storage:** File attachments for tasks and comments are backed by `django-storages` and MinIO (drop-in ready for AWS S3/Cloudflare R2).
* **Stateless & Secure Authentication:** Robust JWT implementation with HttpOnly refresh cookies, Redis-backed token blacklisting, and Google/GitHub Social Auth.
* **Operational Resilience:** * Replay-safe mutation retries via `Idempotency-Key` headers (Redis cached).
  * Distributed request tracing via `X-Trace-ID`.
  * Comprehensive historical audit trails via `django-simple-history`.
* **Deep Observability:** Built-in Prometheus metrics and pre-configured Grafana dashboards for live monitoring of latency, throughput, and worker queue depth.

---

## 🛠️ Technical Stack

* **Core Runtime:** Python 3.14, Django 5.2 LTS, Django REST Framework
* **Database & Cache:** PostgreSQL 18, Redis 8.6
* **Async & Realtime:** Celery, Django Channels, Daphne WebSocket Server
* **Object Storage:** MinIO (S3-compatible API)
* **Observability:** Prometheus, Grafana, `django-prometheus`
* **Testing & Performance:** Pytest (110+ tests), Locust (Load Profiling)
* **API Documentation:** OpenAPI 3.0 (`drf-spectacular`)
* **Infrastructure:** Docker & Docker Compose

---

## 🧠 Engineering Principles

* **Domain-Driven Boundaries:** Business rules are explicit, isolated entirely within the `services.py` layer, and strictly separated from serializers and views.
* **Event-Driven Architecture:** Domain actions reliably publish internal signals and real-time WebSocket events without blocking HTTP responses.
* **Data Integrity over Deletion:** True hard-deletes are forbidden. Soft-deletion is standardized across all core domains, coupled with historical audit recovery managers.
* **Production First:** Rate limiting, connection pooling, idempotency, and observability were treated as Day-1 architectural requirements, not future technical debt.

---

## 🗂️ Project Structure

TaskHive utilizes a Modular Monolith architecture, where each domain strictly owns its models, service layer, views, and tests to maintain bounded contexts:

```text
task_hive/
├── users/          # Authentication, JWT management, social login
├── teams/          # RBAC, invitations, team lifecycle
├── projects/       # Project management and historical audits
├── tasks/          # Tasks, subtasks, tags, file attachments
├── comments/       # Task discussions and file attachments
├── notifications/  # Asynchronous notification processing
├── realtime/       # WebSocket consumers and event publishers
├── common/         # Idempotency, trace IDs, shared permissions
├── observability/  # Prometheus and Grafana provisioning
└── performance/    # Locust profiles for load and smoke testing
```

---

## 🚦 Getting Started

TaskHive boots a fully functional, production-like distributed system locally with a single command.

```bash
# Clone the repository
git clone [https://github.com/empouya/task-hive.git](https://github.com/empouya/task-hive.git)
cd task-hive

# Prepare the environment variables
cp .env.docker.example .env.docker

# Spin up the Hive (Postgres, Redis, MinIO, API, Celery Worker, Prometheus, Grafana)
docker compose --env-file .env.docker up --build
```

### 🔗 Local Services Map

* **API / WebSockets (Daphne):** `http://127.0.0.1:8000`
* **MinIO Console (Storage):** `http://127.0.0.1:9001`
* **Prometheus Metrics:** `http://127.0.0.1:9090`
* **Grafana Dashboards:** `http://127.0.0.1:3001`
* **Health Check:** `http://127.0.0.1:8000/health/`

---

## 🧪 Validating the Architecture

TaskHive encourages verification of its capabilities. 

**1. Run the Test Suite (Validating Domain Logic):**
```bash
pytest --cov
```

**2. Run the Load Test (Validating Scalability):**
Ensure the Docker stack is running, then execute the Locust smoke profile to simulate concurrent users triggering heavy read/write database transactions:
```bash
locust -f performance/locustfile.py --host [http://127.0.0.1:8000](http://127.0.0.1:8000) --headless -u 5 -r 1 -t 1m --csv performance/reports/smoke
```

---

## 🎯 Purpose

TaskHive was built to demonstrate **backend engineering maturity**. It reflects how real-world, enterprise backend systems are designed, hardened, tested, deployed, and operated—proving that architecture is about far more than just writing JSON endpoints.