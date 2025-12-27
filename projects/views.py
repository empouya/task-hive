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

    def get(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        
        # Check if user is a member at all
        is_member = TeamMembership.objects.filter(user=request.user, team=team).exists()
        
        if not is_member:
            return Response(
                {"error": "You do not have access to this team's projects."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        projects = team.projects.filter(status=Project.Status.ACTIVE)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        is_admin = TeamMembership.objects.filter(team=project.team, user=request.user, role=TeamMembership.Role.ADMIN).exists()
        if not is_admin:
            return Response({"error": "Admin rights required for this team."}, status=403)

        if project.status == Project.Status.ARCHIVED:
            return Response(
                {"error": "Archived projects cannot be modified."},
                status=403
            )

        if "status" in request.data:
            return Response(
                {"error": "You're not allowed to change the status of this project!"},
                status=400
            )

        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ProjectArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        is_admin = TeamMembership.objects.filter(team=project.team, user=request.user, role=TeamMembership.Role.ADMIN).exists()
        if not is_admin:
            return Response({"error": "Admin rights required for this team."}, status=403)

        project.status = Project.Status.ARCHIVED
        project.save()
        return Response({"message": "Project archived. It is now read-only."}, status=200)

class ProjectRestoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        is_admin = TeamMembership.objects.filter(team=project.team, user=request.user, role=TeamMembership.Role.ADMIN).exists()
        if not is_admin:
            return Response({"error": "Admin rights required for this team."}, status=403)

        project.status = Project.Status.ACTIVE
        project.save()
        return Response({"message": "Project restored to active status."}, status=200)