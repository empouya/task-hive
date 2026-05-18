from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tasks import services
from tasks.serializers import TaskSerializer


class TaskCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        serializer = TaskSerializer(data=request.data, context={"project": services.get_object_or_404_project(project_id)})
        serializer.is_valid(raise_exception=True)

        task = services.create_task(
            user=request.user,
            project_id=project_id,
            data=serializer.validated_data,
        )
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

    def get(self, request, project_id):
        tasks = services.list_tasks(user=request.user, project_id=project_id)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskReorderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = services.reorder_task(
            user=request.user,
            task_id=task_id,
            target_position=request.data.get("position"),
        )
        return Response({"id": task.id, "position": task.position})


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = services.update_task(
            user=request.user,
            task_id=task_id,
            serializer_class=TaskSerializer,
            data=request.data,
        )
        return Response(TaskSerializer(task).data)

    def delete(self, request, task_id):
        services.delete_task(user=request.user, task_id=task_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = services.assign_task(
            user=request.user,
            task_id=task_id,
            assignee_id=request.data.get("assignee_id"),
        )
        return Response(TaskSerializer(task).data)