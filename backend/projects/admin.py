from django.contrib import admin

from .models import Attachment, Project, StageTransition, Tag, Task, TaskTag, TaskVersion


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "studio", "lead", "status", "project_type", "deadline")
    list_filter = ("status", "project_type", "studio")
    search_fields = ("title", "description")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assignee", "stage", "priority", "version")
    list_filter = ("stage", "priority", "project__studio")
    search_fields = ("title", "description")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "studio", "color")
    list_filter = ("studio",)
    search_fields = ("name",)


@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ("task", "tag")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("filename", "task", "uploaded_by", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("filename", "label")


@admin.register(StageTransition)
class StageTransitionAdmin(admin.ModelAdmin):
    list_display = ("task", "actor", "from_stage", "to_stage", "transitioned_at")
    list_filter = ("from_stage", "to_stage")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TaskVersion)
class TaskVersionAdmin(admin.ModelAdmin):
    list_display = ("task", "version_number", "changed_by", "created_at")
    list_filter = ("created_at",)
