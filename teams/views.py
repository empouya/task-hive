from django.db import transaction
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