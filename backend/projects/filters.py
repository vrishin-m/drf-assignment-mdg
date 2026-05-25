from django.db.models import Q


class TaskFilterSet:
    ordering_fields = {"deadline", "priority", "created_at"}

    def __init__(self, data, queryset):
        self.data = data
        self.queryset = queryset

    @property
    def qs(self):
        qs = self.queryset

        if self.data.get("stage"):
            qs = qs.filter(stage=self.data["stage"])
        if self.data.get("priority"):
            qs = qs.filter(priority=self.data["priority"])
        if self.data.get("assignee"):
            qs = qs.filter(assignee_id=self.data["assignee"])
        if self.data.get("deadline_before"):
            qs = qs.filter(deadline__lte=self.data["deadline_before"])
        if self.data.get("deadline_after"):
            qs = qs.filter(deadline__gte=self.data["deadline_after"])
        if self.data.get("tags"):
            tag_ids = [tag_id.strip() for tag_id in self.data["tags"].split(",") if tag_id.strip()]
            qs = qs.filter(task_tags__tag_id__in=tag_ids).distinct()
        if self.data.get("search"):
            term = self.data["search"]
            qs = qs.filter(Q(title__icontains=term) | Q(description__icontains=term))

        ordering = self.data.get("ordering")
        if ordering:
            raw_field = ordering[1:] if ordering.startswith("-") else ordering
            if raw_field in self.ordering_fields:
                qs = qs.order_by(ordering)

        return qs
