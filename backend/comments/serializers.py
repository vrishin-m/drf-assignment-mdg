from rest_framework import serializers
from .models import Comment
from accounts.models import CustomUser


class CommentAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "full_name",
            "avatar_url",
        )
        read_only_fields = fields


class CommentReadSerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "task",
            "author",
            "body",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body",)

    def validate_body(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Comment body cannot be blank."
            )

        return value


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body",)

    def validate_body(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Comment body cannot be blank."
            )

        return value