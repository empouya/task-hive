import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "task_hive.settings.dev")

app = Celery("task_hive")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()