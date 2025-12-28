from django.urls import path
from .views import TaskDetailView, TaskAssignView, TaskReorderView

urlpatterns = [
    path('<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:task_id>/assign/', TaskAssignView.as_view(), name='task-assign'),
    path('<int:task_id>/reorder/', TaskReorderView.as_view(), name='task-reorder'),
]