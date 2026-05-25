from rest_framework import serializers

from .models import Notification
from accounts.models import CustomUser


class NotificationActorSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "full_name",
            "avatar_url",
        )
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):

    actor = NotificationActorSerializer(
        read_only=True
    )

    class Meta:
        model = Notification

        fields = (
            "id",
            "actor",
            "event_type",
            "payload",
            "is_read",
            "created_at",
        )

        read_only_fields = fields