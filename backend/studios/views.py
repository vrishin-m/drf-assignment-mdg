from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Studio, Membership, Role
from .serializers import StudioSerializer, MembershipSerializer
from .permissions import IsStudioAdmin, IsStudioMember

class StudioViewSet(viewsets.ModelViewSet):
    serializer_class = StudioSerializer
    permission_classes = [IsAuthenticated]

    lookup_field = "slug"

    def get_permissions(self):
        permission_map = {
            "update": [IsStudioAdmin],
            "partial_update": [IsStudioAdmin],
            "destroy": [IsStudioAdmin],
            "members": [IsStudioAdmin if self.request.method == "POST" else IsStudioMember],
            "member_detail": [IsStudioAdmin],
            "my_membership": [IsStudioMember],
        }
        permission_classes = permission_map.get(self.action, self.permission_classes)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Studio.objects.filter(
            memberships__user=self.request.user,
            is_active=True
        ).distinct()

    def perform_create(self, serializer):
        studio = serializer.save()
        Membership.objects.create(
            studio=studio,
            user=self.request.user,
            role='studio_admin'
        )

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="members",
        url_name="member-list",
    )
    def members(self, request, slug=None):
        studio = self.get_object()

        if request.method == "POST":
            user_id = request.data.get("user")
            role = request.data.get("role", Role.DESIGNER)

            if role not in Role.values:
                return Response(
                    {"role": "Invalid role."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            User = get_user_model()
            user = get_object_or_404(User, id=user_id)

            membership, created = Membership.objects.get_or_create(
                studio=studio,
                user=user,
                defaults={"role": role}
            )

            if not created:
                return Response(
                    {"detail": "User is already a member."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                MembershipSerializer(membership).data,
                status=status.HTTP_201_CREATED
            )

        qs = studio.memberships.select_related("user")
        return Response(
            MembershipSerializer(qs, many=True).data
        )
    
    @action(
        detail=True,
        methods=["get"],
        url_path="members/me",
        url_name="my-membership",
    )
    def my_membership(self, request, slug=None):
        studio = self.get_object()

        membership = get_object_or_404(
            Membership,
            studio=studio,
            user=request.user
        )

        return Response(
            MembershipSerializer(membership).data
        )

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"members/(?P<user_id>[0-9a-fA-F-]{36})",
        url_name="member-detail",
    )
    def member_detail(self, request, slug=None, user_id=None):

        membership = get_object_or_404(
            Membership,
            user_id=user_id,
            studio__slug=slug
        )

        if request.method == "PATCH":
            new_role = request.data.get("role")

            if (
                membership.user == request.user
                and membership.role == Role.STUDIO_ADMIN
                and new_role
                and new_role != Role.STUDIO_ADMIN
                and not self._has_another_admin(membership)
            ):
                return Response(
                    {"detail": "Cannot demote the only studio admin."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = MembershipSerializer(
                membership,
                data=request.data,
                partial=True
            )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)

        if (
            membership.user == request.user
            and membership.role == Role.STUDIO_ADMIN
            and not self._has_another_admin(membership)
        ):
            return Response(
                {"detail": "Cannot remove the only studio admin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsStudioAdmin])
    def add_member(self, request, slug=None):
        studio = self.get_object()
        email = request.data.get('email')
        role  = request.data.get('role', 'designer')

        if role not in Role.values:
            return Response(
                {"role": "Invalid role."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            User = get_user_model()
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'No user with that email exists.'}, status=404)

        membership, created = Membership.objects.get_or_create(
            studio=studio,
            user=user,
            defaults={'role': role}
        )
        if not created:
            return Response({'detail': 'User is already a member.'}, status=400)

        return Response(MembershipSerializer(membership).data, status=201)

    def _has_another_admin(self, membership):
        return Membership.objects.filter(
            studio=membership.studio,
            role=Role.STUDIO_ADMIN
        ).exclude(id=membership.id).exists()
 
