import random
import uuid

from locust import HttpUser, between, task


class TaskHiveUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        unique = uuid.uuid4().hex[:10]
        self.email = f"load-{unique}@taskhive.local"
        self.password = "StrongPass123"
        self.access_token = None
        self.team_id = None
        self.project_id = None
        self.task_ids = []

        self.register()
        self.login()
        self.create_team()
        self.create_project()

    def auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def register(self):
        self.client.post(
            "/api/v1/auth/register/",
            json={
                "email": self.email,
                "password": self.password,
                "password_confirm": self.password,
            },
            name="auth:register",
        )

    def login(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            json={
                "email": self.email,
                "password": self.password,
            },
            name="auth:login",
        )
        if response.ok:
            payload = response.json()
            self.access_token = payload["data"]["access"]

    def create_team(self):
        response = self.client.post(
            "/api/v1/teams/",
            headers=self.auth_headers(),
            json={
                "name": f"Load Team {uuid.uuid4().hex[:8]}",
                "description": "Created by Locust",
            },
            name="teams:create",
        )
        if response.ok:
            self.team_id = response.json()["data"]["id"]

    def create_project(self):
        if not self.team_id:
            return

        response = self.client.post(
            f"/api/v1/teams/{self.team_id}/projects/",
            headers=self.auth_headers(),
            json={
                "name": f"Load Project {uuid.uuid4().hex[:8]}",
                "description": "Created by Locust",
            },
            name="projects:create",
        )
        if response.ok:
            self.project_id = response.json()["data"]["id"]

    @task(5)
    def list_projects(self):
        if not self.team_id:
            return

        self.client.get(
            f"/api/v1/teams/{self.team_id}/projects/",
            headers=self.auth_headers(),
            name="projects:list",
        )

    @task(5)
    def list_tasks(self):
        if not self.project_id:
            return

        self.client.get(
            f"/api/v1/projects/{self.project_id}/tasks/",
            headers=self.auth_headers(),
            name="tasks:list",
        )

    @task(2)
    def create_task(self):
        if not self.project_id:
            return

        response = self.client.post(
            f"/api/v1/projects/{self.project_id}/tasks/",
            headers={
                **self.auth_headers(),
                "Idempotency-Key": str(uuid.uuid4()),
            },
            json={
                "title": f"Load Task {uuid.uuid4().hex[:8]}",
                "description": "Created by Locust",
            },
            name="tasks:create",
        )

        if response.ok:
            self.task_ids.append(response.json()["data"]["id"])

    @task(2)
    def update_task(self):
        if not self.task_ids:
            return

        task_id = random.choice(self.task_ids)
        self.client.patch(
            f"/api/v1/tasks/{task_id}/",
            headers={
                **self.auth_headers(),
                "Idempotency-Key": str(uuid.uuid4()),
            },
            json={
                "status": random.choice(["TODO", "IN_PROGRESS", "DONE"]),
            },
            name="tasks:update",
        )

    @task(1)
    def comment_on_task(self):
        if not self.task_ids:
            return

        task_id = random.choice(self.task_ids)
        self.client.post(
            f"/api/v1/tasks/{task_id}/comments/",
            headers={
                **self.auth_headers(),
                "Idempotency-Key": str(uuid.uuid4()),
            },
            json={
                "content": f"Load comment {uuid.uuid4().hex[:8]}",
            },
            name="comments:create",
        )