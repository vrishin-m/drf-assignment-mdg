from rest_framework.permissions import BasePermission

from studios.models import Membership, Role


WRITE_ROLES = [
    Role.STUDIO_ADMIN,
    Role.PROJECT_LEAD,
    Role.DESIGNER,
    Role.WRITER,
    Role.REVIEWER,
]


def get_membership_for_slug(user, slug):
    if not user or not user.is_authenticated:
        return None
    return Membership.objects.select_related("studio").filter(
        user=user,
        studio__slug=slug,
    ).first()


def has_role(user, slug, roles):
    membership = get_membership_for_slug(user, slug)
    return bool(membership and membership.role in roles)


class StudioMemberPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))


class ProjectPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))
        if request.method == "POST":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])
        if request.method == "DELETE":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN])
        return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.method == "DELETE":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN])
        return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])


class TaskPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))
        if request.method == "POST":
            return has_role(request.user, view.kwargs.get("slug"), WRITE_ROLES)
        if request.method == "DELETE":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])
        return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.method == "DELETE":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])
        return (
            obj.assignee_id == request.user.id
            or has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])
        )


class TransitionPermission(BasePermission):
    def has_permission(self, request, view):
        membership = get_membership_for_slug(request.user, view.kwargs.get("slug"))
        return bool(membership and membership.role != Role.CLIENT_VIEWER)


class AttachmentPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))
        if request.method == "POST":
            return has_role(request.user, view.kwargs.get("slug"), WRITE_ROLES)
        return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.uploaded_by_id == request.user.id or has_role(
            request.user,
            view.kwargs.get("slug"),
            [Role.STUDIO_ADMIN],
        )


class TagPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return bool(get_membership_for_slug(request.user, view.kwargs.get("slug")))
        if request.method == "POST":
            return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN, Role.PROJECT_LEAD])
        return has_role(request.user, view.kwargs.get("slug"), [Role.STUDIO_ADMIN])
