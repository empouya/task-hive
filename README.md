# TaskHive — Team/Project Management (Django REST Backend)

TaskHive is a **Django REST API** for team-based project and task management.
It was built to simulate a real backend engineering lifecycle — from requirements clarification to deployment and observability — with a strong focus on **clean architecture, explicit business rules, and operational readiness**.


[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-6.0-green.svg)](https://www.djangoproject.com/)
[![Test Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Key Features

- **Team-based access control**
  - Users can belong to multiple teams
  - Role-based permissions (`admin`, `member`)
- **Projects & Tasks**
  - Projects scoped to teams
  - Tasks with status, priority, due dates, and global ordering per project
- **Explicit business logic**
  - Domain rules enforced outside serializers
  - Strict team and permission boundaries
- **Comments & Notifications**
  - Task comments visible to project members
  - In-app notifications for assignments and comments
- **Soft-delete–aware data integrity**
- **Stateless authentication**
  - JWT-based auth

---

## 🛠️ Technical Stack

- **Framework:** Django + Django REST Framework  
- **Database:** PostgreSQL  
- **Authentication:** JWT (stateless)  
- **Architecture:** Modular monolith  
- **Testing:** Pytest (unit + integration)  
- **Coverage:** ~96% overall, 100% on core domains  
- **API Docs:** OpenAPI (drf-spectacular)  
- **Deployment:** Docker & Docker Compose  
- **Observability:** Structured logging + health checks

---

## 🧠 Engineering Principles

- Business rules are explicit and testable
- Behavior is validated by tests, not implementation details
- State transitions use dedicated endpoints
- Architecture stability before feature expansion
- Production concerns addressed early

---

## 🗂️ Project Structure (High-Level)

```
task_hive/
├── users/
├── teams/
├── projects/
├── tasks/
├── comments/
├── notifications/
├── common/         # shared permissions, exceptions, logging
├── task_hive/      # configurations
```

Each domain owns its models, services, views, and tests.

---

## 🚦 Getting Started

TaskHive is designed to boot in a production-like environment with a single command.

```bash
# Clone the repository
git clone [https://github.com/empouya/task-hive.git](https://github.com/empouya/task-hive.git)
cd task-hive

# Spin up the Hive (Gunicorn + Postgres + WhiteNoise)
docker-compose up --build
```

This setup includes:
- Gunicorn application server
- PostgreSQL database
- Environment-driven configuration
- Health check endpoint available at `/health/`

---

## 🧪 Testing

```bash
pytest
```

The test suite includes:
- Unit tests for domain and service logic
- Integration tests for API endpoints
- Full coverage of critical business paths (teams → projects → tasks)

---

## 📌 Project Status

- ✅ Feature complete
- ✅ Fully tested
- ✅ Dockerized
- ✅ Production-ready (local)

This project is considered **complete** and maintained as a reference implementation of a clean, production-grade Django REST backend.

---

## 🎯 Purpose

TaskHive was built to demonstrate **backend engineering maturity**, including:

- Domain modeling and system design
- Permission and data-integrity enforcement
- Test discipline and quality hardening
- Deployment and operational awareness

It reflects how real-world backend systems are **designed, built, tested, deployed, and operated** — not just how endpoints are written.
