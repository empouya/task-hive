from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Team, TeamMembership, Invitation
from .serializers import TeamSerializer

class TeamCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                team = serializer.save()
                TeamMembership.objects.create(
                    user=request.user,
                    team=team,
                    role=TeamMembership.Role.ADMIN
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user_teams = Team.objects.filter(memberships__user=request.user)
        serializer = TeamSerializer(
            user_teams, 
            many=True, 
            context={'request': request} 
        )
        return Response(serializer.data)

class TeamDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, team_id, user):
        team = get_object_or_404(Team, id=team_id)
        is_admin = TeamMembership.objects.filter(
            team=team, 
            user=user, 
            role=TeamMembership.Role.ADMIN
        ).exists()
        
        if not is_admin:
            return None
        return team

    def patch(self, request, team_id):
        team = self.get_object(team_id, request.user)
        if not team:
            return Response({"error": "Admin rights required"}, status=403)

        serializer = TeamSerializer(team, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, team_id):
        team = self.get_object(team_id, request.user)
        if not team:
            return Response({"error": "Admin rights required"}, status=403)

        team.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        is_admin = TeamMembership.objects.filter(team=team, user=request.user, role=TeamMembership.Role.ADMIN).exists()
        if not is_admin:
            return Response({"error": "Admin rights required"}, status=403)

        email = request.data.get('email')

        if not email:
            return Response({"error": "Email is required"}, status=400)

        if TeamMembership.objects.filter(team=team, user__email=email).exists():
            return Response({"error": "User is already a member"}, status=400)

        invitation, created = Invitation.objects.update_or_create(
            team=team, email=email,
            defaults={'invited_by': request.user, 'created_at': timezone.now()}
        )

        return Response({
            "message": "Invitation sent",
            "token": invitation.token
        }, status=201)

class AcceptInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        if not invitation.is_valid():
            return Response({"error": "Invitation is invalid or expired"}, status=400)
        
        if invitation.email != request.user.email:
            return Response({"error": "This invitation was not intended for this user"}, status=403)

        with transaction.atomic():
            TeamMembership.objects.get_or_create(
                team=invitation.team,
                user=request.user,
                defaults={'role': TeamMembership.Role.MEMBER}
            )
            invitation.accepted_at = timezone.now()
            invitation.save()

        return Response({"message": f"Successfully joined {invitation.team.name}"})

    def delete(self, request, team_id, invite_id):
        team = get_object_or_404(Team, id=team_id)
        is_admin = TeamMembership.objects.filter(team=team, user=request.user, role=TeamMembership.Role.ADMIN).exists()
        if not is_admin:
            return Response({"error": "Admin rights required"}, status=403)

        invitation = get_object_or_404(Invitation, id=invite_id, team_id=team_id)
        invitation.delete()
        return Response(status=204)
