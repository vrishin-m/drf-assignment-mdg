from .models import Notification


def notify(
    recipient,
    actor,
    event_type,
    payload
):
    if recipient is None:
        return

    if recipient == actor:
        return

    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        event_type=event_type,
        payload=payload
    )


def _base_payload(task, actor):

    return {
        "task_id": str(task.id),
        "task_title": task.title,

        "project_id": str(task.project.id),
        "project_name": task.project.title,

        "actor_name": actor.full_name
    }


def notify_task_assigned(
    task,
    actor
):
    if task.assignee is None:
        return

    payload = _base_payload(
        task,
        actor
    )

    notify(
        recipient=task.assignee,
        actor=actor,
        event_type=Notification.TASK_ASSIGNED,
        payload=payload
    )


def notify_stage_changed(
    task,
    actor,
    from_stage,
    to_stage
):

    payload = _base_payload(
        task,
        actor
    )

    payload["extra"] = (
        f"{from_stage} → {to_stage}"
    )

    recipients = [
        task.assignee,
        task.project.lead
    ]

    for recipient in recipients:
        notify(
            recipient=recipient,
            actor=actor,
            event_type=Notification.STAGE_CHANGED,
            payload=payload
        )


def notify_comment_added(
    comment,
    actor
):

    task = comment.task

    payload = _base_payload(
        task,
        actor
    )

    payload["extra"] = comment.body[:120]

    recipients = [
        task.assignee,
        task.project.lead
    ]

    for recipient in recipients:
        notify(
            recipient=recipient,
            actor=actor,
            event_type=Notification.COMMENT_ADDED,
            payload=payload
        )


def notify_attachment_uploaded(
    attachment,
    actor
):

    task = attachment.task

    payload = _base_payload(
        task,
        actor
    )

    notify(
        recipient=task.assignee,
        actor=actor,
        event_type=Notification.ATTACHMENT_UPLOADED,
        payload=payload
    )