from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "task",
        "created_at",
    )

    search_fields = (
        "body",
        "author__email",
    )

    list_filter = (
        "created_at",
    )
