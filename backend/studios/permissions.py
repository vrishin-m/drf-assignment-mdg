from rest_framework.permissions import BasePermission
from .models import Membership, Role, Studio


ROLE_HIERARCHY = [
    Role.CLIENT_VIEWER,
    Role.WRITER,
    Role.DESIGNER,
    Role.REVIEWER,
    Role.PROJECT_LEAD,
    Role.STUDIO_ADMIN,
]


def get_membership(user, studio_slug):

    if not user.is_authenticated:
        return None

    try:
        studio = Studio.objects.get(slug=studio_slug)

        return Membership.objects.get(
            user=user,
            studio=studio
        )

    except (Membership.DoesNotExist, Studio.DoesNotExist):
        return None


def has_role(user, studio_slug, *roles):
    m = get_membership(user, studio_slug)
    return m and m.role in roles


def has_min_role(user, studio_slug, min_role):
    m = get_membership(user, studio_slug)

    if not m:
        return False

    return (
        ROLE_HIERARCHY.index(m.role)
        >= ROLE_HIERARCHY.index(min_role)
    )


class IsStudioMember(BasePermission):
    def has_permission(self, request, view):
        studio_slug = view.kwargs.get("slug")
        return bool(
            get_membership(
                request.user,
                studio_slug
            )
        )


class IsStudioAdmin(BasePermission):
    def has_permission(self, request, view):
        studio_slug = view.kwargs.get("slug")

        return has_role(
            request.user,
            studio_slug,
            Role.STUDIO_ADMIN
        )


class IsProjectLeadOrAbove(BasePermission):
    def has_permission(self, request, view):
        studio_slug = view.kwargs.get("slug")

        return has_min_role(
            request.user,
            studio_slug,
            Role.PROJECT_LEAD
        )


class IsReviewerOrAbove(BasePermission):
    def has_permission(self, request, view):
        studio_slug = view.kwargs.get("slug")

        return has_min_role(
            request.user,
            studio_slug,
            Role.REVIEWER
        )


class CannotWrite(BasePermission):
    def has_permission(self, request, view):

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        studio_slug = view.kwargs.get("slug")

        return has_min_role(
            request.user,
            studio_slug,
            Role.WRITER
        )