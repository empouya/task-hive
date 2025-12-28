from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from tasks.models import Task
from .serializers import CommentSerializer
from .models import Comment
from teams.models import TeamMembership


class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        
        if not task.project.team.memberships.filter(user=request.user).exists():
            return Response(status=403)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, task=task)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        team = comment.task.project.team

        is_admin = TeamMembership.objects.filter(
            user=request.user, 
            team=team, 
            role=TeamMembership.Role.ADMIN
        ).exists()

        if not is_admin:
            return Response(
                {"error": "Only team admins can moderate (delete) comments."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
