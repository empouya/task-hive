from django.urls import path
from .views import ProjectCreateListView, ProjectDetailView, ProjectArchiveView, ProjectRestoreView

urlpatterns = [
    path('<int:team_id>/projects/', ProjectCreateListView.as_view(), name='project-list-create'),
    path('<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:project_id>/archive/', ProjectArchiveView.as_view(), name='project-archive'),
    path('<int:project_id>/restore/', ProjectRestoreView.as_view(), name='project-restore'),
]