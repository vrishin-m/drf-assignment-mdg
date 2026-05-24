# studios/models.py
import uuid
from django.db import models
from django.conf import settings

class Studio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)         
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Role(models.TextChoices):
    STUDIO_ADMIN   = 'studio_admin',   'Studio Admin'
    PROJECT_LEAD   = 'project_lead',   'Project Lead'
    DESIGNER       = 'designer',       'Designer'
    WRITER         = 'writer',         'Writer'
    REVIEWER       = 'reviewer',       'Reviewer'
    CLIENT_VIEWER  = 'client_viewer',  'Client Viewer'


class Membership(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    studio     = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='memberships')
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    role       = models.CharField(max_length=30, choices=Role.choices, default=Role.DESIGNER)
    joined_at  = models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ('studio', 'user')   

    def __str__(self):
        return f"{self.user} @ {self.studio} ({self.role})"

