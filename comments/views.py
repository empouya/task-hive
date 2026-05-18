from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comments import services
from comments.serializers import CommentSerializer


class CommentCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = services.create_comment(
            user=request.user,
            task_id=task_id,
            data=serializer.validated_data,
        )
        payload = CommentSerializer(comment).data
        payload["author"] = {
            "id": str(request.user.id),
            "email": request.user.email,
        }
        return Response(payload, status=status.HTTP_201_CREATED)

    def get(self, request, task_id):
        comments = services.list_comments(user=request.user, task_id=task_id)
        payload = CommentSerializer(comments, many=True).data

        for index, comment in enumerate(comments):
            payload[index]["author"] = {
                "id": str(comment.author.id),
                "email": comment.author.email,
            }

        return Response(payload)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, comment_id):
        services.delete_comment(user=request.user, comment_id=comment_id)
        return Response(status=status.HTTP_204_NO_CONTENT)