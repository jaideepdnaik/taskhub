from django.utils import timezone
from rest_framework import serializers
from .models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    task_count = serializers.IntegerField(read_only=True)  # comes from annotate()

    class Meta:
        model = Project
        fields = ["id", "name", "owner", "task_count", "created_at"]


class TaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)            # output: nested objects
    tag_ids = serializers.PrimaryKeyRelatedField(              # input: list of ids
        queryset=Tag.objects.all(), many=True, write_only=True,
        source="tags", required=False,
    )
    assignee_name = serializers.CharField(
        source="assignee.username", read_only=True, default=None
    )
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "project", "title", "description", "status", "priority",
            "assignee", "assignee_name", "tags", "tag_ids", "due_date",
            "is_overdue", "completed_at", "created_at",
        ]
        read_only_fields = ["completed_at", "created_at"]

    def get_is_overdue(self, obj):
        return bool(
            obj.due_date
            and obj.status != Task.Status.DONE
            and obj.due_date < timezone.localdate()
        )

    def validate_title(self, value):                 # field-level
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value

    def validate(self, attrs):                        # cross-field / object-level
        due = attrs.get("due_date")
        if due and due < timezone.localdate():
            raise serializers.ValidationError({"due_date": "Due date cannot be in the past."})
        return attrs