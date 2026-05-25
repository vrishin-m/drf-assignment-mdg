import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from studios.models import Membership, Role, Studio


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"
    COMPLETED = "completed", "Completed"


class ProjectType(models.TextChoices):
    POSTER = "poster", "Poster"
    VIDEO = "video", "Video"
    CAMPAIGN = "campaign", "Campaign"
    CONTENT = "content", "Content"
    OTHER = "other", "Other"


class TaskStage(models.TextChoices):
    DRAFT = "draft", "Draft"
    REVIEW = "review", "Review"
    REVISION = "revision", "Revision"
    APPROVED = "approved", "Approved"
    COMPLETED = "completed", "Completed"


class TaskPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name="projects")
    lead = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="led_projects")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.OTHER)
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["studio", "status"]),
            models.Index(fields=["studio", "deadline"]),
            models.Index(fields=["lead"]),
        ]

    def clean(self):
        super().clean()
        membership = Membership.objects.filter(studio=self.studio, user=self.lead).first()
        if not membership:
            raise ValidationError({"lead": "Lead must belong to the same studio."})
        if membership.role not in (Role.PROJECT_LEAD, Role.STUDIO_ADMIN):
            raise ValidationError({"lead": "Lead must be a project lead or studio admin."})

    def __str__(self):
        return self.title


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tasks")
    stage = models.CharField(max_length=20, choices=TaskStage.choices, default=TaskStage.DRAFT)
    priority = models.CharField(max_length=20, choices=TaskPriority.choices, default=TaskPriority.MEDIUM)
    deadline = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "stage"]),
            models.Index(fields=["project", "priority"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["deadline"]),
        ]

    def clean(self):
        super().clean()
        if self.assignee and not Membership.objects.filter(
            studio=self.project.studio,
            user=self.assignee,
        ).exists():
            raise ValidationError({"assignee": "Assignee must belong to the same studio."})

    def __str__(self):
        return self.title


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=80)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["studio", "name"], name="unique_tag_name_per_studio"),
        ]
        indexes = [
            models.Index(fields=["studio", "name"]),
        ]

    def clean(self):
        super().clean()
        if not self.color.startswith("#") or len(self.color) != 7:
            raise ValidationError({"color": "Color must be a #RRGGBB hex string."})

    def __str__(self):
        return self.name


class TaskTag(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="task_tags")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "tag"], name="unique_tag_per_task"),
        ]
        indexes = [
            models.Index(fields=["task", "tag"]),
        ]

    def clean(self):
        super().clean()
        if self.task.project.studio_id != self.tag.studio_id:
            raise ValidationError({"tag": "Tag must belong to the task studio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task} - {self.tag}"


class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_attachments")
    file_url = models.URLField()
    filename = models.CharField(max_length=255)
    label = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["task", "uploaded_at"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def __str__(self):
        return self.filename


class StageTransitionQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise ValidationError("Stage transition history is append-only.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Stage transition history is append-only.")


class StageTransitionManager(models.Manager):
    def get_queryset(self):
        return StageTransitionQuerySet(self.model, using=self._db)


class StageTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="stage_transitions")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_transitions")
    from_stage = models.CharField(max_length=20, choices=TaskStage.choices)
    to_stage = models.CharField(max_length=20, choices=TaskStage.choices)
    reason = models.TextField(blank=True)
    transitioned_at = models.DateTimeField(auto_now_add=True)

    objects = StageTransitionManager()

    class Meta:
        ordering = ["-transitioned_at"]
        indexes = [
            models.Index(fields=["task", "transitioned_at"]),
            models.Index(fields=["actor"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk and StageTransition.objects.filter(pk=self.pk).exists():
            raise ValidationError("Stage transition history is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Stage transition history is append-only.")


class TaskVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="task_versions")
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(fields=["task", "version_number"], name="unique_version_per_task"),
        ]
        indexes = [
            models.Index(fields=["task", "version_number"]),
        ]

    def __str__(self):
        return f"{self.task} v{self.version_number}"
