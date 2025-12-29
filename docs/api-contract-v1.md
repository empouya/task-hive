# Task Hive API v1 – Contract Freeze

## Users
- POST /api/v1/auth/register/
- POST /api/v1/auth/login/
- POST /api/v1/auth/logout/
- POST /api/v1/auth/token/refresh/
- GET /api/v1/auth/me/

## Teams
- CRUD endpoints
- Membership management
- Invitations

## Projects
- CRUD
- Archiving
- Deletion

## Tasks
- CRUD
- Assignment
- Status transitions

## Comments
- CRUD

## Notifications
- List + mark as read

## Rules
- All endpoints require authentication unless stated
- Admin-only operations enforced
- JWT Bearer authentication
