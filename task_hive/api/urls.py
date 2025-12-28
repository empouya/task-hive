from django.urls import path
from projects.views import ProjectCreateListView
from tasks.views import TaskCreateListView
from comments.views import CommentCreateListView

urlpatterns = [
    # projects urls
    path('teams/<int:team_id>/projects/', ProjectCreateListView.as_view(), name='project-create-list'),

    # tasks urls
    path('projects/<int:project_id>/tasks/', TaskCreateListView.as_view(), name='task-create-list'),

    # comments urls
    path('tasks/<int:task_id>/comments/', CommentCreateListView.as_view(), name='comment-create-list'),
]