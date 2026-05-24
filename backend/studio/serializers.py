from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Studio, Membership

class StudioSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Studio
        fields = ['id', 'name', 'slug', 'description', 'member_count']
        read_only_fields = ['id']

    def get_member_count(self, obj):
        return obj.memberships.count()


class MembershipSerializer(serializers.ModelSerializer):
    user_email    = serializers.EmailField(source='user.email', read_only=True)
    user_name     = serializers.CharField(source='user.get_full_name', read_only=True)
    role_display  = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'user_email', 'user_name', 'role', 'role_display', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'user_email', 'user_name']


