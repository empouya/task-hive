from django.urls import path
from .views import ProjectDetailView, ProjectArchiveView, ProjectRestoreView

urlpatterns = [
    path('<int:project_id>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:project_id>/archive/', ProjectArchiveView.as_view(), name='project-archive'),
    path('<int:project_id>/restore/', ProjectRestoreView.as_view(), name='project-restore'),
]