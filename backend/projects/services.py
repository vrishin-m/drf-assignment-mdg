from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from studios.models import Membership, Role

from .models import StageTransition, Task, TaskStage, TaskVersion


ALLOWED_TRANSITIONS = {
    TaskStage.DRAFT: [TaskStage.REVIEW],
    TaskStage.REVIEW: [TaskStage.REVISION, TaskStage.APPROVED],
    TaskStage.REVISION: [TaskStage.REVIEW],
    TaskStage.APPROVED: [TaskStage.COMPLETED],
    TaskStage.COMPLETED: [],
}


TRANSITION_ROLES = {
    (TaskStage.DRAFT, TaskStage.REVIEW): [Role.DESIGNER, Role.WRITER, Role.PROJECT_LEAD],
    (TaskStage.REVIEW, TaskStage.REVISION): [Role.REVIEWER, Role.PROJECT_LEAD, Role.STUDIO_ADMIN],
    (TaskStage.REVIEW, TaskStage.APPROVED): [Role.REVIEWER, Role.PROJECT_LEAD, Role.STUDIO_ADMIN],
    (TaskStage.REVISION, TaskStage.REVIEW): [Role.DESIGNER, Role.WRITER, Role.PROJECT_LEAD],
    (TaskStage.APPROVED, TaskStage.COMPLETED): [Role.PROJECT_LEAD, Role.STUDIO_ADMIN],
}


def get_studio_membership(user, studio):
    if not user or not user.is_authenticated:
        return None
    return Membership.objects.filter(user=user, studio=studio).first()


def require_studio_role(user, studio, allowed_roles):
    membership = get_studio_membership(user, studio)
    if not membership or membership.role not in allowed_roles:
        raise ValidationError("You do not have permission to perform this transition.")
    return membership


@transaction.atomic
def transition_task(task, to_stage, actor, reason=""):
    task = (
        Task.objects
        .select_for_update()
        .select_related("project__studio")
        .get(pk=task.pk)
    )
    from_stage = task.stage

    if to_stage not in ALLOWED_TRANSITIONS.get(from_stage, []):
        raise ValidationError(f"Cannot transition task from {from_stage} to {to_stage}.")

    allowed_roles = TRANSITION_ROLES.get((from_stage, to_stage), [])
    require_studio_role(actor, task.project.studio, allowed_roles)

    StageTransition.objects.create(
        task=task,
        actor=actor,
        from_stage=from_stage,
        to_stage=to_stage,
        reason=reason or "",
    )

    if from_stage == TaskStage.REVIEW and to_stage == TaskStage.APPROVED:
        save_version_snapshot(task, actor)
        task.version = F("version") + 1

    task.stage = to_stage
    task.save(update_fields=["version", "stage"])
    task.refresh_from_db()
    return task


def save_version_snapshot(task, actor):
    tag_names = list(
        task.task_tags.select_related("tag")
        .order_by("tag__name")
        .values_list("tag__name", flat=True)
    )
    snapshot = {
        "title": task.title,
        "description": task.description,
        "assignee": str(task.assignee_id) if task.assignee_id else None,
        "priority": task.priority,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "stage": task.stage,
        "tags": tag_names,
        "changed_by": str(actor.id),
    }
    return TaskVersion.objects.create(
        task=task,
        version_number=task.version,
        changed_by=actor,
        snapshot=snapshot,
    )
