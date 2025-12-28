from django.urls import path
from .views import TaskCreateView, TaskReorderView, TaskListView, TaskDetailView, TaskAssignView

urlpatterns = [
    path('<int:project_id>/', TaskCreateView.as_view(), name='task-create'),
    path('<int:task_id>/reorder/', TaskReorderView.as_view(), name='task-reorder'),
    path('projects/<int:project_id>/tasks/', TaskListView.as_view(), name='task-list'),
    path('task/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:task_id>/assign/', TaskAssignView.as_view(), name='task-assign'),
]