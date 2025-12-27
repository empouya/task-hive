from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Team, TeamMembership
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
