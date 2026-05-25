from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Notification
from .serializers import NotificationSerializer


class NotificationPagination(PageNumberPagination):
    page_size = 20


class NotificationViewSet(ReadOnlyModelViewSet):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            "actor"
        )


    @action(
        detail=True,
        methods=["post"],
        url_path="read"
    )
    def mark_read(
        self,
        request,
        pk=None
    ):
        notification = self.get_object()

        if not notification.is_read:
            notification.is_read = True

            notification.save(
                update_fields=["is_read"]
            )

        serializer = self.get_serializer(
            notification
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


    @action(
        detail=False,
        methods=["post"],
        url_path="read-all"
    )
    def mark_all_read(
        self,
        request
    ):
        queryset = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )

        count = queryset.count()

        queryset.update(
            is_read=True
        )

        return Response(
            {"marked_read": count},
            status=status.HTTP_200_OK
        )


    @action(
        detail=False,
        methods=["get"],
        url_path="unread-count"
    )
    def unread_count(
        self,
        request
    ):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return Response(
            {"count": count},
            status=status.HTTP_200_OK
        )
