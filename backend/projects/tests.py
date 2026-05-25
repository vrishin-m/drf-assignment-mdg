from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from studios.models import Membership, Role, Studio

from .filters import TaskFilterSet
from .models import Project, StageTransition, Tag, Task, TaskStage, TaskTag, TaskVersion
from .services import transition_task


User = get_user_model()


def create_user(email, full_name="Test User"):
    return User.objects.create_user(email=email, password="StrongPass123!", full_name=full_name)


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class ProjectTestCase(APITestCase):
    def setUp(self):
        self.studio = Studio.objects.create(name="Project Studio", slug="project-studio")
        self.admin = create_user("admin@example.com")
        self.lead = create_user("lead@example.com")
        self.designer = create_user("designer@example.com")
        self.writer = create_user("writer@example.com")
        self.reviewer = create_user("reviewer@example.com")
        self.viewer = create_user("viewer@example.com")
        self.outsider = create_user("outsider@example.com")
        Membership.objects.create(studio=self.studio, user=self.admin, role=Role.STUDIO_ADMIN)
        Membership.objects.create(studio=self.studio, user=self.lead, role=Role.PROJECT_LEAD)
        Membership.objects.create(studio=self.studio, user=self.designer, role=Role.DESIGNER)
        Membership.objects.create(studio=self.studio, user=self.writer, role=Role.WRITER)
        Membership.objects.create(studio=self.studio, user=self.reviewer, role=Role.REVIEWER)
        Membership.objects.create(studio=self.studio, user=self.viewer, role=Role.CLIENT_VIEWER)
        self.project = Project.objects.create(
            studio=self.studio,
            lead=self.lead,
            title="Launch",
            description="Launch work",
            project_type="campaign",
            deadline=timezone.now() + timedelta(days=7),
            created_by=self.admin,
        )

    def test_project_lead_must_belong_to_studio_and_have_lead_role(self):
        project = Project(
            studio=self.studio,
            lead=self.designer,
            title="Invalid",
            deadline=timezone.now() + timedelta(days=1),
            created_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            project.clean()

    def test_project_create_endpoint_allows_project_lead(self):
        response = auth_client(self.lead).post(
            reverse("project-list", kwargs={"slug": self.studio.slug}),
            {
                "lead": str(self.lead.id),
                "title": "New Campaign",
                "project_type": "campaign",
                "deadline": (timezone.now() + timedelta(days=10)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_viewer_cannot_create_project(self):
        response = auth_client(self.viewer).post(
            reverse("project-list", kwargs={"slug": self.studio.slug}),
            {
                "lead": str(self.lead.id),
                "title": "Nope",
                "deadline": (timezone.now() + timedelta(days=10)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_project_lead_or_admin_can_patch_project(self):
        url = reverse("project-detail", kwargs={"slug": self.studio.slug, "id": self.project.id})

        for user in [self.designer, self.writer, self.reviewer, self.viewer]:
            response = auth_client(user).patch(url, {"title": "Blocked"})
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                msg=f"{user.email} should not patch projects",
            )

        response = auth_client(self.lead).patch(url, {"title": "Lead Update"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Lead Update")

    def test_studio_admin_can_delete_project(self):
        url = reverse("project-detail", kwargs={"slug": self.studio.slug, "id": self.project.id})
        response = auth_client(self.admin).delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TaskWorkflowTestCase(APITestCase):
    def setUp(self):
        self.studio = Studio.objects.create(name="Workflow Studio", slug="workflow-studio")
        self.admin = create_user("admin@example.com")
        self.lead = create_user("lead@example.com")
        self.designer = create_user("designer@example.com")
        self.reviewer = create_user("reviewer@example.com")
        self.viewer = create_user("viewer@example.com")
        Membership.objects.create(studio=self.studio, user=self.admin, role=Role.STUDIO_ADMIN)
        Membership.objects.create(studio=self.studio, user=self.lead, role=Role.PROJECT_LEAD)
        Membership.objects.create(studio=self.studio, user=self.designer, role=Role.DESIGNER)
        Membership.objects.create(studio=self.studio, user=self.reviewer, role=Role.REVIEWER)
        Membership.objects.create(studio=self.studio, user=self.viewer, role=Role.CLIENT_VIEWER)
        self.project = Project.objects.create(
            studio=self.studio,
            lead=self.lead,
            title="Workflow",
            deadline=timezone.now() + timedelta(days=7),
            created_by=self.admin,
        )
        self.task = Task.objects.create(
            project=self.project,
            title="Poster",
            description="Draft poster",
            assignee=self.designer,
            created_by=self.lead,
        )

    def test_task_assignee_must_belong_to_studio(self):
        outsider = create_user("outsider@example.com")
        task = Task(project=self.project, title="Bad", assignee=outsider, created_by=self.admin)
        with self.assertRaises(ValidationError):
            task.clean()

    def test_transition_creates_history_but_version_only_on_approval(self):
        transition_task(self.task, "review", self.designer, "Ready")
        self.task.refresh_from_db()
        self.assertEqual(self.task.stage, "review")
        self.assertEqual(self.task.version, 1)
        self.assertEqual(StageTransition.objects.count(), 1)
        self.assertEqual(TaskVersion.objects.count(), 0)

        transition_task(self.task, "approved", self.reviewer, "Approved")
        self.task.refresh_from_db()
        self.assertEqual(self.task.stage, "approved")
        self.assertEqual(self.task.version, 2)
        self.assertEqual(TaskVersion.objects.count(), 1)
        self.assertEqual(TaskVersion.objects.get().snapshot["stage"], "review")

    def test_duplicate_review_to_approved_request_does_not_create_duplicate_version(self):
        transition_task(self.task, "review", self.designer, "Ready")
        transition_task(self.task, "approved", self.reviewer, "Approved")

        with self.assertRaises(ValidationError):
            transition_task(self.task, "approved", self.reviewer, "Duplicate")

        self.task.refresh_from_db()
        self.assertEqual(self.task.stage, "approved")
        self.assertEqual(self.task.version, 2)
        self.assertEqual(TaskVersion.objects.count(), 1)
        self.assertEqual(StageTransition.objects.count(), 2)

    def test_client_viewer_cannot_transition(self):
        with self.assertRaises(ValidationError):
            transition_task(self.task, "review", self.viewer, "No")

    def test_task_filters_stage_priority_tags_and_search(self):
        tag = Tag.objects.create(studio=self.studio, name="Poster", color="#ff00aa")
        self.task.priority = "urgent"
        self.task.save()
        self.task.task_tags.create(tag=tag)
        qs = TaskFilterSet(
            {
                "stage": "draft",
                "priority": "urgent",
                "tags": str(tag.id),
                "search": "poster",
                "ordering": "-created_at",
            },
            Task.objects.all(),
        ).qs
        self.assertEqual(list(qs), [self.task])

    def test_task_serializer_uses_prefetched_tags_without_n_plus_one(self):
        from .serializers import TaskSerializer

        tag = Tag.objects.create(studio=self.studio, name="Design", color="#ff00aa")
        for index in range(3):
            task = Task.objects.create(
                project=self.project,
                title=f"Task {index}",
                created_by=self.lead,
            )
            task.task_tags.create(tag=tag)

        qs = Task.objects.filter(project=self.project).prefetch_related("task_tags__tag")
        with self.assertNumQueries(3):
            TaskSerializer(qs, many=True, context={"project": self.project, "request": None}).data

    def test_tasktag_create_rejects_cross_studio_tag(self):
        other_studio = Studio.objects.create(name="Other", slug="other")
        other_tag = Tag.objects.create(studio=other_studio, name="Wrong", color="#111111")

        with self.assertRaises(ValidationError):
            TaskTag.objects.create(task=self.task, tag=other_tag)

    def test_stage_transition_queryset_update_and_delete_are_blocked(self):
        transition_task(self.task, "review", self.designer, "Ready")

        with self.assertRaises(ValidationError):
            StageTransition.objects.filter(task=self.task).update(reason="mutated")

        with self.assertRaises(ValidationError):
            StageTransition.objects.filter(task=self.task).delete()

    def test_project_stats_include_empty_stages_total_and_overdue_count(self):
        Task.objects.create(
            project=self.project,
            title="Overdue",
            created_by=self.lead,
            deadline=timezone.now() - timedelta(days=1),
        )
        Task.objects.create(
            project=self.project,
            title="Completed overdue",
            created_by=self.lead,
            stage=TaskStage.COMPLETED,
            deadline=timezone.now() - timedelta(days=2),
        )
        response = auth_client(self.lead).get(
            reverse("project-stats", kwargs={"slug": self.studio.slug, "id": self.project.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["task_count"], 3)
        self.assertEqual(response.data["overdue_count"], 1)
        self.assertEqual(
            response.data["by_stage"],
            {
                "draft": 2,
                "review": 0,
                "revision": 0,
                "approved": 0,
                "completed": 1,
            },
        )

    def test_task_endpoint_create_and_transition(self):
        task_url = reverse("task-list", kwargs={"slug": self.studio.slug, "id": self.project.id})
        response = auth_client(self.designer).post(
            task_url,
            {
                "title": "Copy",
                "description": "Write copy",
                "assignee": str(self.designer.id),
                "priority": "high",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.data["id"]
        transition_url = reverse(
            "task-transition",
            kwargs={"slug": self.studio.slug, "id": self.project.id, "task_id": task_id},
        )
        response = auth_client(self.designer).post(transition_url, {"to_stage": "review"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stage"], "review")

    def test_task_update_permission_allows_assignee_not_viewer(self):
        detail_url = reverse(
            "task-detail",
            kwargs={"slug": self.studio.slug, "id": self.project.id, "task_id": self.task.id},
        )
        self.assertEqual(auth_client(self.designer).patch(detail_url, {"title": "Updated"}).status_code, status.HTTP_200_OK)
        self.assertEqual(auth_client(self.viewer).patch(detail_url, {"title": "Blocked"}).status_code, status.HTTP_403_FORBIDDEN)

    def test_tag_and_attachment_endpoints(self):
        tag_url = reverse("tag-list", kwargs={"slug": self.studio.slug})
        response = auth_client(self.lead).post(tag_url, {"name": "Design", "color": "#123abc"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tag_id = response.data["id"]
        response = auth_client(self.lead).patch(reverse("tag-detail", kwargs={"slug": self.studio.slug, "id": tag_id}), {"name": "Nope"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        attachment_url = reverse(
            "attachment-list",
            kwargs={"slug": self.studio.slug, "id": self.project.id, "task_id": self.task.id},
        )
        response = auth_client(self.designer).post(
            attachment_url,
            {"file_url": "https://example.com/file.png", "filename": "file.png", "label": "draft"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        att_id = response.data["id"]
        delete_url = reverse(
            "attachment-detail",
            kwargs={"slug": self.studio.slug, "id": self.project.id, "task_id": self.task.id, "att_id": att_id},
        )
        self.assertEqual(auth_client(self.designer).delete(delete_url).status_code, status.HTTP_204_NO_CONTENT)
