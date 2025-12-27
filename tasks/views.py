from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from projects.models import Project
from teams.models import Team, TeamMembership
from .serializers import TaskSerializer

class TaskCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        team = project.team

        if not TeamMembership.objects.filter(user=request.user, team=team).exists():
            return Response({"error": "You are not a member of this team."}, status=403)

        if project.status == Project.Status.ARCHIVED:
            return Response({"error": "Cannot create tasks in an archived project."}, status=400)

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            assignee = serializer.validated_data.get('assignee')
            if assignee and not TeamMembership.objects.filter(user=assignee, team=team).exists():
                return Response({"error": "Assignee must be a member of the team."}, status=400)

            max_pos = project.tasks.aggregate(Max('position'))['position__max'] or 0
            
            serializer.save(
                project=project,
                creator=request.user,
                position=max_pos + 1.0
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
