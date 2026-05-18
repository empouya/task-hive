from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from teams import services
from teams.serializers import TeamSerializer


class TeamCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team = services.create_team(
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(
            TeamSerializer(team, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        teams = services.list_user_teams(user=request.user)
        serializer = TeamSerializer(teams, many=True, context={"request": request})
        return Response(serializer.data)


class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, team_id):
        team = services.update_team(
            user=request.user,
            team_id=team_id,
            serializer_class=TeamSerializer,
            data=request.data,
        )
        return Response(TeamSerializer(team, context={"request": request}).data)

    def delete(self, request, team_id):
        services.soft_delete_team(user=request.user, team_id=team_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        invitation = services.create_invitation(
            user=request.user,
            team_id=team_id,
            email=request.data.get("email"),
        )
        return Response(_invitation_payload(invitation), status=status.HTTP_201_CREATED)

    def get(self, request, team_id):
        invitations = services.list_pending_invitations(
            user=request.user,
            team_id=team_id,
        )
        return Response([_invitation_payload(invitation) for invitation in invitations])


class AcceptInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = services.accept_invitation(user=request.user, token=token)
        return Response({"message": f"Successfully joined {invitation.team.name}"})

    def delete(self, request, team_id, invite_id):
        services.delete_invitation(
            user=request.user,
            team_id=team_id,
            invite_id=invite_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamMemberManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, team_id):
        memberships = services.list_members(user=request.user, team_id=team_id)
        return Response([
            {
                "id": membership.user.id,
                "email": membership.user.email,
                "role": membership.role,
            }
            for membership in memberships
        ])

    def delete(self, request, team_id, user_id):
        services.remove_member(
            user=request.user,
            team_id=team_id,
            user_id=user_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def _invitation_payload(invitation):
    return {
        "id": str(invitation.id),
        "email": invitation.email,
        "token": str(invitation.token),
        "created_at": invitation.created_at.isoformat(),
    }