from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects import services
from projects.serializers import ProjectSerializer


class ProjectCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, team_id):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = services.create_project(
            user=request.user,
            team_id=team_id,
            data=serializer.validated_data,
        )
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)

    def get(self, request, team_id):
        projects = services.list_projects(user=request.user, team_id=team_id)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, project_id):
        project = services.update_project(
            user=request.user,
            project_id=project_id,
            serializer_class=ProjectSerializer,
            data=request.data,
        )
        return Response(ProjectSerializer(project).data)


class ProjectArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        services.archive_project(user=request.user, project_id=project_id)
        return Response({"message": "Project archived. It is now read-only."}, status=status.HTTP_200_OK)


class ProjectRestoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        services.restore_project(user=request.user, project_id=project_id)
        return Response({"message": "Project restored to active status."}, status=status.HTTP_200_OK)