from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from teams.models import TeamMembership, Team
from .models import Project
from .serializers import ProjectSerializer

class ProjectCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        
        is_admin = TeamMembership.objects.filter(
            user=request.user, 
            team=team, 
            role=TeamMembership.Role.ADMIN
        ).exists()

        if not is_admin:
            return Response(
                {"error": "Only team admins can create projects."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(team=team)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
