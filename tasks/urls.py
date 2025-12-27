from django.urls import path
from .views import TaskCreateView

urlpatterns = [
    path('tasks/<int:project_id>/', TaskCreateView.as_view(), name='task-create'),
]