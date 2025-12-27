from django.urls import path
from .views import TaskCreateView, TaskReorderView

urlpatterns = [
    path('tasks/<int:project_id>/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:task_id>/reorder/', TaskReorderView.as_view(), name='task-reorder'),
]