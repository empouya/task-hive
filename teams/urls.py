from django.urls import path
from .views import TeamCreateListView, TeamDetailView

urlpatterns = [
    path('', TeamCreateListView.as_view(), name='team-list-create'),
    path('<int:team_id>/', TeamDetailView.as_view(), name='team-detail')
]