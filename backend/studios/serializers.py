from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Studio, Membership


User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']

class StudioSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Studio
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'member_count']
        read_only_fields = ['id', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.count()


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    user_email    = serializers.EmailField(source='user.email', read_only=True)
    user_name     = serializers.CharField(source='user.full_name', read_only=True)
    role_display  = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'user_email', 'user_name', 'role', 'role_display', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'user_email', 'user_name']
