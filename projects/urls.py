from django.urls import path
from .views import ProjectCreateListView

urlpatterns = [
    path('<int:team_id>/projects/', ProjectCreateListView.as_view(), name='project-list-create'),
]