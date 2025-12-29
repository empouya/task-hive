from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Max
from projects.models import Project
from teams.models import Team, TeamMembership
from .serializers import TaskSerializer
from .services import TaskService
from .models import Task

services = TaskService

class TaskCreateListView(APIView):
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

    
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        
        if not TeamMembership.objects.filter(user=request.user, team=project.team).exists():
            return Response(status=403)

        tasks = project.tasks.all().order_by('position')
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

class TaskReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        if task.project.status == Project.Status.ARCHIVED:
            return Response({"error": "Project is archived"}, status=403)

        new_position = request.data.get('position')

        if not TeamMembership.objects.filter(
            user=request.user, 
            team=task.project.team
        ).exists():
            return Response(status=status.HTTP_403_FORBIDDEN)

        if new_position is None:
            return Response({"error": "Position is required"}, status=400)

        services.reorder_task(task, new_position)

        return Response({"id": task.id, "position": task.position})

class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_task_and_check_access(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        is_member = TeamMembership.objects.filter(
            user=request.user, 
            team=task.project.team
        ).exists()
        
        if not is_member:
            return None, Response({"error": "Access denied"}, status=403)
            
        if task.project.status == Project.Status.ARCHIVED:
            return None, Response({"error": "Project is archived"}, status=403)
            
        return task, None

    def patch(self, request, task_id):
        task, error_res = self.get_task_and_check_access(request, task_id)
        if error_res: return error_res

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, task_id):
        task, error_res = self.get_task_and_check_access(request, task_id)
        if error_res: return error_res

        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TaskAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        
        is_admin = TeamMembership.objects.filter(
            user=request.user, 
            team=task.project.team, 
            role=TeamMembership.Role.ADMIN
        ).exists()
        if not is_admin:
            return Response({"error": "Only admins can reassign tasks."}, status=403)

        new_assignee_id = request.data.get('assignee_id')
        if new_assignee_id:
            if not TeamMembership.objects.filter(user_id=new_assignee_id, team=task.project.team).exists():
                return Response({"error": "User is not in this team."}, status=400)
            task.assignee_id = new_assignee_id
        else:
            task.assignee = None
            
        task.save()
        return Response(TaskSerializer(task).data)
