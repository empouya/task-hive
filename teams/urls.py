from django.urls import path
from .views import TeamCreateListView, TeamDetailView, InvitationView, AcceptInvitationView, TeamMemberManagementView

urlpatterns = [
    path('', TeamCreateListView.as_view(), name='team-list-create'),
    path('<int:team_id>/', TeamDetailView.as_view(), name='team-detail'),
    path('<int:team_id>/invites/<int:invite_id>/', AcceptInvitationView.as_view(), name="invite-delete"),
    path('<int:team_id>/invites/', InvitationView.as_view(), name='invite-create'),
    path('<int:team_id>/members/', TeamMemberManagementView.as_view(), name='team-member-list'),
    path('<int:team_id>/members/<int:user_id>', TeamMemberManagementView.as_view(), name='team-member-remove'),
]