from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from tasks.models import Task
from .serializers import CommentSerializer
from .models import Comment
from teams.models import TeamMembership
from projects.models import Project


class CommentCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        
        if not task.project.team.memberships.filter(user=request.user).exists():
            return Response(status=403)

        if task.project.status == Project.Status.ARCHIVED:
            return Response({"error": "Project is archived"}, status=403)

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, task=task)
            payload = serializer.data
        
            payload['author'] = {
                'id': str(request.user.id),
                'email': request.user.email
            }
            return Response(payload, status=201)
        return Response(serializer.errors, status=400)

    def get(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        
        if not task.project.team.memberships.filter(user=request.user).exists():
            return Response(status=403)

        comments = task.comments.select_related('author').all().order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        payload = serializer.data

        for i, comment_obj in enumerate(comments):
            payload[i]['author'] = {
                'id': str(comment_obj.author.id),
                'email': comment_obj.author.email,
            }

        return Response(payload)

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
