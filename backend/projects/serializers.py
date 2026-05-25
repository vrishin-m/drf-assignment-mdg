from rest_framework import serializers
from django.db import transaction

from .models import Attachment, Project, StageTransition, Tag, Task, TaskTag, TaskVersion


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "studio",
            "lead",
            "title",
            "description",
            "status",
            "project_type",
            "deadline",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "studio", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        data = {
            "lead": attrs.get("lead", getattr(self.instance, "lead", None)),
            "title": attrs.get("title", getattr(self.instance, "title", "")),
            "description": attrs.get("description", getattr(self.instance, "description", "")),
            "status": attrs.get("status", getattr(self.instance, "status", "active")),
            "project_type": attrs.get("project_type", getattr(self.instance, "project_type", "other")),
            "deadline": attrs.get("deadline", getattr(self.instance, "deadline", None)),
        }
        instance = Project(**data)
        instance.studio = self.context["studio"]
        instance.created_by = self.context["request"].user
        instance.clean()
        return attrs


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "studio", "name", "color"]
        read_only_fields = ["id", "studio"]

    def validate(self, attrs):
        instance = Tag(
            name=attrs.get("name", getattr(self.instance, "name", "")),
            color=attrs.get("color", getattr(self.instance, "color", "")),
        )
        instance.studio = self.context["studio"]
        instance.clean()
        return attrs


class TaskSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    tag_details = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "assignee",
            "created_by",
            "stage",
            "priority",
            "deadline",
            "version",
            "created_at",
            "updated_at",
            "tags",
            "tag_details",
        ]
        read_only_fields = ["id", "project", "created_by", "stage", "version", "created_at", "updated_at"]

    def validate(self, attrs):
        project = self.context["project"]
        instance = Task(
            title=attrs.get("title", getattr(self.instance, "title", "")),
            description=attrs.get("description", getattr(self.instance, "description", "")),
            assignee=attrs.get("assignee", getattr(self.instance, "assignee", None)),
            stage=getattr(self.instance, "stage", "draft"),
            priority=attrs.get("priority", getattr(self.instance, "priority", "medium")),
            deadline=attrs.get("deadline", getattr(self.instance, "deadline", None)),
        )
        instance.project = project
        instance.created_by = self.context["request"].user
        instance.clean()

        tag_ids = attrs.get("tags", [])
        if tag_ids:
            found_count = Tag.objects.filter(studio=project.studio, id__in=tag_ids).count()
            if found_count != len(set(tag_ids)):
                raise serializers.ValidationError({"tags": "All tags must belong to the project studio."})
        return attrs

    def get_tag_details(self, obj):
        tags = [task_tag.tag for task_tag in obj.task_tags.all()]
        tags.sort(key=lambda tag: tag.name)
        return TagSerializer(tags, many=True).data

    def create(self, validated_data):
        with transaction.atomic():
            tag_ids = validated_data.pop("tags", [])
            task = Task.objects.create(
                project=self.context["project"],
                created_by=self.context["request"].user,
                **validated_data,
            )
            self._sync_tags(task, tag_ids)
            return task

    def update(self, instance, validated_data):
        with transaction.atomic():
            tag_ids = validated_data.pop("tags", None)
            for key, value in validated_data.items():
                setattr(instance, key, value)
            instance.clean()
            instance.save()
            if tag_ids is not None:
                instance.task_tags.all().delete()
                self._sync_tags(instance, tag_ids)
            return instance

    def _sync_tags(self, task, tag_ids):
        for tag in Tag.objects.filter(studio=task.project.studio, id__in=tag_ids):
            TaskTag.objects.create(task=task, tag=tag)


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "task", "uploaded_by", "file_url", "filename", "label", "uploaded_at"]
        read_only_fields = ["id", "task", "uploaded_by", "uploaded_at"]


class StageTransitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StageTransition
        fields = ["id", "task", "actor", "from_stage", "to_stage", "reason", "transitioned_at"]


class TaskVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskVersion
        fields = ["id", "task", "version_number", "changed_by", "snapshot", "created_at"]


class TransitionSerializer(serializers.Serializer):
    to_stage = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
