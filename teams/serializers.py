from rest_framework import serializers
from .models import Team, TeamMembership

class TeamSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'role', 'created_at']

    def get_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return None
            
        membership = obj.memberships.filter(user=request.user).first()
        return membership.role if membership else None