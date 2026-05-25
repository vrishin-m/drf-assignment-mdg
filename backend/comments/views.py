from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Comment
from .serializers import (
    CommentReadSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
)
from .permissions import (
    IsStudioMember,
    CanPostComment,
    IsCommentAuthorOrAdmin,
)

from projects.models import Task
from notifications.utils import notify_comment_added


class CommentPagination(PageNumberPagination):
    page_size = 20


class CommentViewSet(ModelViewSet):

    pagination_class = CommentPagination

    http_method_names = [
        "get",
        "post",
        "patch",
        "delete",
    ]

    def get_task(self):
        return get_object_or_404(
            Task.objects.select_related(
                "project",
                "project__studio",
            ),
            id=self.kwargs["task_id"],
            project_id=self.kwargs["project_id"],
            project__studio__slug=self.kwargs["slug"],
        )

    def get_queryset(self):
        task = self.get_task()

        return Comment.objects.filter(
            task=task
        ).select_related(
            "author",
            "task__project__studio",
        )

    def get_permissions(self):

        if self.action in ["list", "retrieve"]:
            permission_classes = [
                IsAuthenticated,
                IsStudioMember,
            ]

        elif self.action == "create":
            permission_classes = [
                IsAuthenticated,
                CanPostComment,
            ]

        elif self.action in ["partial_update", "destroy"]:
            permission_classes = [
                IsAuthenticated,
                IsStudioMember,
                IsCommentAuthorOrAdmin,
            ]

        else:
            permission_classes = [IsAuthenticated]

        return [
            permission()
            for permission in permission_classes
        ]

    def get_serializer_class(self):

        if self.action == "create":
            return CommentCreateSerializer

        elif self.action == "partial_update":
            return CommentUpdateSerializer

        return CommentReadSerializer

    def perform_create(self, serializer):
        task = self.get_task()

        comment = serializer.save(
            task=task,
            author=self.request.user
        )

        notify_comment_added(
            comment,
            self.request.user
        )

        return comment

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = self.perform_create(serializer)
        read_serializer = CommentReadSerializer(
            comment,
            context=self.get_serializer_context(),
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True

        return super().update(
            request,
            *args,
            **kwargs
        )
