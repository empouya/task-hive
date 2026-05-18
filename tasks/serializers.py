from rest_framework import serializers

from tasks.models import Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "parent",
            "tags",
            "position",
            "created_at",
        ]
        read_only_fields = ["position"]

    def validate(self, attrs):
        project = self.instance.project if self.instance else self.context.get("project")
        parent = attrs.get("parent")

        if project and parent and parent.project_id != project.id:
            raise serializers.ValidationError({
                "parent": "Parent task must belong to the same project.",
            })

        tags = attrs.get("tags", [])
        invalid_tags = [tag.id for tag in tags if project and tag.project_id != project.id]
        if invalid_tags:
            raise serializers.ValidationError({
                "tags": "Tags must belong to the same project as the task.",
            })

        return attrs