from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.ReadOnlyField(source='actor.username')
    task_title = serializers.ReadOnlyField(source='target_task.title')

    class Meta:
        model = Notification
        fields = ['id', 'actor_name', 'verb', 'task_title', 'target_task', 'unread', 'created_at']