from rest_framework.permissions import BasePermission

from projects.models import Task
from studios.models import Membership, Role


def get_task_from_view(view):
    return Task.objects.select_related(
        "project",
        "project__studio",
    ).filter(
        id=view.kwargs.get("task_id"),
        project_id=view.kwargs.get("project_id"),
        project__studio__slug=view.kwargs.get("slug"),
    ).first()


def get_membership(user, studio):
    if not user or not user.is_authenticated or studio is None:
        return None
    return Membership.objects.filter(
        studio=studio,
        user=user,
    ).first()


class IsStudioMember(BasePermission):

    def has_permission(self, request, view):
        task = get_task_from_view(view)
        studio = task.project.studio if task else None

        return bool(get_membership(request.user, studio))

class CanPostComment(BasePermission):
    """
    Any member except client_viewer
    """

    def has_permission(self, request, view):
        task = get_task_from_view(view)
        studio = task.project.studio if task else None

        membership = get_membership(request.user, studio)

        if not membership:
            return False

        return membership.role != Role.CLIENT_VIEWER


class IsCommentAuthorOrAdmin(BasePermission):
    """
    PATCH → only author
    DELETE → author or admin
    """

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):
        if request.method in ["PATCH"]:
            return obj.author == request.user

        if request.method == "DELETE":
            if obj.author == request.user:
                return True

            membership = get_membership(
                request.user,
                obj.task.project.studio,
            )

            return (
                membership
                and membership.role == Role.STUDIO_ADMIN
            )

        return False
