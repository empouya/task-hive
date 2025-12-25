from rest_framework import serializers
from .models import Team, TeamMembership

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at']