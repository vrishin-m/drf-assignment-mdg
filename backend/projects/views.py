from django.db.models import Count
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from studios.models import Studio

from .filters import TaskFilterSet
from .models import Attachment, Project, Tag, Task, TaskStage, TaskVersion
from .permissions import (
    AttachmentPermission,
    ProjectPermission,
    StudioMemberPermission,
    TagPermission,
    TaskPermission,
    TransitionPermission,
)
from .serializers import (
    AttachmentSerializer,
    ProjectSerializer,
    TagSerializer,
    TaskSerializer,
    TaskVersionSerializer,
    TransitionSerializer,
)
from .services import transition_task


def get_studio(slug):
    return get_object_or_404(Studio, slug=slug, is_active=True)


def project_queryset():
    return Project.objects.select_related("studio", "lead", "created_by").prefetch_related("tasks")


def task_queryset():
    return Task.objects.select_related("project", "project__studio", "assignee", "created_by").prefetch_related(
        "task_tags__tag",
        "attachments",
    )


class ProjectListCreateView(APIView):
    permission_classes = [ProjectPermission]

    def get(self, request, slug):
        studio = get_studio(slug)
        qs = project_queryset().filter(studio=studio)
        return Response(ProjectSerializer(qs, many=True, context={"studio": studio, "request": request}).data)

    def post(self, request, slug):
        studio = get_studio(slug)
        serializer = ProjectSerializer(data=request.data, context={"studio": studio, "request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save(studio=studio, created_by=request.user)
        return Response(ProjectSerializer(project, context={"studio": studio, "request": request}).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    permission_classes = [ProjectPermission]

    def get_object(self, slug, id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        return studio, project

    def get(self, request, slug, id):
        studio, project = self.get_object(slug, id)
        return Response(ProjectSerializer(project, context={"studio": studio, "request": request}).data)

    def patch(self, request, slug, id):
        studio, project = self.get_object(slug, id)
        self.check_object_permissions(request, project)
        serializer = ProjectSerializer(project, data=request.data, partial=True, context={"studio": studio, "request": request})
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return Response(ProjectSerializer(project, context={"studio": studio, "request": request}).data)

    def delete(self, request, slug, id):
        studio, project = self.get_object(slug, id)
        self.check_object_permissions(request, project)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectStatsView(APIView):
    permission_classes = [StudioMemberPermission]

    def get(self, request, slug, id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        rows = project.tasks.values("stage").annotate(count=Count("id"))
        by_stage = {stage: 0 for stage in TaskStage.values}
        for row in rows:
            by_stage[row["stage"]] = row["count"]
        task_count = sum(by_stage.values())
        overdue_count = project.tasks.filter(
            deadline__lt=timezone.now()
        ).exclude(stage=TaskStage.COMPLETED).count()
        return Response(
            {
                "project": str(project.id),
                "task_count": task_count,
                "overdue_count": overdue_count,
                "by_stage": by_stage,
            }
        )


class TaskListCreateView(APIView):
    permission_classes = [TaskPermission]

    def get_project(self, slug, id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        return studio, project

    def get(self, request, slug, id):
        studio, project = self.get_project(slug, id)
        qs = task_queryset().filter(project=project)
        qs = TaskFilterSet(request.query_params, qs).qs
        serializer = TaskSerializer(qs, many=True, context={"project": project, "request": request})
        return Response(serializer.data)

    def post(self, request, slug, id):
        studio, project = self.get_project(slug, id)
        serializer = TaskSerializer(data=request.data, context={"project": project, "request": request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task, context={"project": project, "request": request}).data, status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    permission_classes = [TaskPermission]

    def get_objects(self, slug, id, task_id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        return studio, project, task

    def get(self, request, slug, id, task_id):
        studio, project, task = self.get_objects(slug, id, task_id)
        return Response(TaskSerializer(task, context={"project": project, "request": request}).data)

    def patch(self, request, slug, id, task_id):
        studio, project, task = self.get_objects(slug, id, task_id)
        self.check_object_permissions(request, task)
        serializer = TaskSerializer(task, data=request.data, partial=True, context={"project": project, "request": request})
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task, context={"project": project, "request": request}).data)

    def delete(self, request, slug, id, task_id):
        studio, project, task = self.get_objects(slug, id, task_id)
        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskTransitionView(APIView):
    permission_classes = [TransitionPermission]

    def post(self, request, slug, id, task_id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task = transition_task(
                task,
                serializer.validated_data["to_stage"],
                request.user,
                serializer.validated_data.get("reason", ""),
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(str(exc))
        return Response(TaskSerializer(task, context={"project": project, "request": request}).data)


class TaskVersionListView(APIView):
    permission_classes = [StudioMemberPermission]

    def get(self, request, slug, id, task_id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        qs = TaskVersion.objects.select_related("task", "changed_by").filter(task=task)
        return Response(TaskVersionSerializer(qs, many=True).data)


class TaskVersionDetailView(APIView):
    permission_classes = [StudioMemberPermission]

    def get(self, request, slug, id, task_id, version_number):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        version = get_object_or_404(TaskVersion.objects.select_related("task", "changed_by"), task=task, version_number=version_number)
        return Response(TaskVersionSerializer(version).data)


class AttachmentListCreateView(APIView):
    permission_classes = [AttachmentPermission]

    def get_task(self, slug, id, task_id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        return task

    def get(self, request, slug, id, task_id):
        task = self.get_task(slug, id, task_id)
        qs = Attachment.objects.select_related("task", "uploaded_by").filter(task=task)
        return Response(AttachmentSerializer(qs, many=True).data)

    def post(self, request, slug, id, task_id):
        task = self.get_task(slug, id, task_id)
        serializer = AttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(task=task, uploaded_by=request.user)
        return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class AttachmentDeleteView(APIView):
    permission_classes = [AttachmentPermission]

    def delete(self, request, slug, id, task_id, att_id):
        studio = get_studio(slug)
        project = get_object_or_404(project_queryset(), studio=studio, id=id)
        task = get_object_or_404(task_queryset(), project=project, id=task_id)
        attachment = get_object_or_404(Attachment.objects.select_related("uploaded_by", "task"), task=task, id=att_id)
        self.check_object_permissions(request, attachment)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagListCreateView(APIView):
    permission_classes = [TagPermission]

    def get(self, request, slug):
        studio = get_studio(slug)
        qs = Tag.objects.filter(studio=studio)
        return Response(TagSerializer(qs, many=True, context={"studio": studio}).data)

    def post(self, request, slug):
        studio = get_studio(slug)
        serializer = TagSerializer(data=request.data, context={"studio": studio})
        serializer.is_valid(raise_exception=True)
        tag = serializer.save(studio=studio)
        return Response(TagSerializer(tag, context={"studio": studio}).data, status=status.HTTP_201_CREATED)


class TagDetailView(APIView):
    permission_classes = [TagPermission]

    def get_object(self, slug, id):
        studio = get_studio(slug)
        return studio, get_object_or_404(Tag, studio=studio, id=id)

    def patch(self, request, slug, id):
        studio, tag = self.get_object(slug, id)
        serializer = TagSerializer(tag, data=request.data, partial=True, context={"studio": studio})
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        return Response(TagSerializer(tag, context={"studio": studio}).data)

    def delete(self, request, slug, id):
        studio, tag = self.get_object(slug, id)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
