import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):

    TASK_ASSIGNED = "task_assigned"
    STAGE_CHANGED = "stage_changed"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_UPLOADED = "attachment_uploaded"

    EVENT_CHOICES = [
        (TASK_ASSIGNED, "Task Assigned"),
        (STAGE_CHANGED, "Stage Changed"),
        (COMMENT_ADDED, "Comment Added"),
        (ATTACHMENT_UPLOADED, "Attachment Uploaded"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications"
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_CHOICES
    )

    payload = models.JSONField(
        default=dict
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} - {self.event_type}"
