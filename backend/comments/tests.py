from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(email, password="StrongPass123!", full_name="Test User"):
    return User.objects.create_user(email=email, password=password, full_name=full_name)


def auth_client(user):
    client = APIClient()
    token  = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def comments_url(slug, project_id, task_id):
    return reverse(
        "comment-list",
        kwargs={"slug": slug, "project_id": project_id, "task_id": task_id},
    )


def comment_detail_url(slug, project_id, task_id, comment_id):
    return reverse(
        "comment-detail",
        kwargs={
            "slug": slug,
            "project_id": project_id,
            "task_id": task_id,
            "pk": comment_id,
        },
    )


# ---------------------------------------------------------------------------
# Fixtures mixin — creates studio, project, task, and three members
# ---------------------------------------------------------------------------

class CommentFixtureMixin:
    """
    Sets up:
      self.studio   — a studio
      self.project  — a project inside that studio
      self.task     — a task inside that project
      self.admin    — studio_admin
      self.designer — designer (task assignee)
      self.viewer   — client_viewer
      self.outsider — not a member at all
    """

    def _setup_fixtures(self):
        from studios.models import Studio, StudioMembership
        from projects.models import Project, Task

        self.admin    = create_user("admin@x.com")
        self.designer = create_user("designer@x.com")
        self.viewer   = create_user("viewer@x.com")
        self.outsider = create_user("outsider@x.com")

        self.admin_client    = auth_client(self.admin)
        self.designer_client = auth_client(self.designer)
        self.viewer_client   = auth_client(self.viewer)
        self.outsider_client = auth_client(self.outsider)

        self.studio = Studio.objects.create(name="Test Studio", slug="test-studio")

        for user, role in [
            (self.admin,    "studio_admin"),
            (self.designer, "designer"),
            (self.viewer,   "client_viewer"),
        ]:
            StudioMembership.objects.create(studio=self.studio, user=user, role=role)

        self.project = Project.objects.create(
            studio=self.studio,
            lead=self.admin,
            title="Test Project",
            created_by=self.admin,
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.task = Task.objects.create(
            project=self.project,
            title="Test Task",
            assignee=self.designer,
            created_by=self.admin,
            stage="draft",
            priority="medium",
        )

        self.slug       = self.studio.slug
        self.project_id = self.project.id
        self.task_id    = self.task.id

        self.list_url   = comments_url(self.slug, self.project_id, self.task_id)


# ---------------------------------------------------------------------------
# 1. List comments
# ---------------------------------------------------------------------------

class CommentListTestCase(CommentFixtureMixin, APITestCase):

    def setUp(self):
        self._setup_fixtures()
        from .models import Comment
        Comment.objects.create(task=self.task, author=self.admin,    body="First comment")
        Comment.objects.create(task=self.task, author=self.designer, body="Second comment")

    def test_member_can_list_comments(self):
        response = self.designer_client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_client_viewer_can_list_comments(self):
        response = self.viewer_client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_cannot_list_comments(self):
        response = self.outsider_client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_list_comments(self):
        response = APIClient().get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comments_are_ordered_oldest_first(self):
        response = self.admin_client.get(self.list_url)
        bodies = [c["body"] for c in response.data["results"]]
        self.assertEqual(bodies[0], "First comment")
        self.assertEqual(bodies[1], "Second comment")

    def test_response_contains_author_info(self):
        response = self.admin_client.get(self.list_url)
        comment  = response.data["results"][0]
        self.assertIn("author", comment)
        self.assertIn("full_name", comment["author"])

    def test_response_is_paginated(self):
        response = self.admin_client.get(self.list_url)
        self.assertIn("results", response.data)
        self.assertIn("count",   response.data)


# ---------------------------------------------------------------------------
# 2. Create comment
# ---------------------------------------------------------------------------

class CommentCreateTestCase(CommentFixtureMixin, APITestCase):

    def setUp(self):
        self._setup_fixtures()

    def test_member_can_post_comment(self):
        response = self.designer_client.post(self.list_url, {"body": "Looking good!"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_post_comment(self):
        response = self.admin_client.post(self.list_url, {"body": "Please revise section 2."})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_client_viewer_cannot_post_comment(self):
        response = self.viewer_client.post(self.list_url, {"body": "Looks nice"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_post_comment(self):
        response = self.outsider_client.post(self.list_url, {"body": "Intruding"})
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_post_comment(self):
        response = APIClient().post(self.list_url, {"body": "Anonymous"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blank_body_returns_400(self):
        response = self.designer_client.post(self.list_url, {"body": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_whitespace_only_body_returns_400(self):
        response = self.designer_client.post(self.list_url, {"body": "   "})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_body_returns_400(self):
        response = self.designer_client.post(self.list_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_author_is_set_to_request_user(self):
        response = self.designer_client.post(self.list_url, {"body": "My comment"})
        self.assertEqual(response.data["author"]["full_name"], self.designer.full_name)

    def test_comment_is_associated_with_correct_task(self):
        from .models import Comment
        self.designer_client.post(self.list_url, {"body": "Task comment"})
        comment = Comment.objects.get(body="Task comment")
        self.assertEqual(comment.task, self.task)

    def test_response_does_not_contain_other_tasks_comments(self):
        from projects.models import Task
        other_task = Task.objects.create(
            project=self.project,
            title="Other Task",
            created_by=self.admin,
            stage="draft",
            priority="low",
        )
        other_url = comments_url(self.slug, self.project_id, other_task.id)
        self.designer_client.post(other_url, {"body": "Other task comment"})
        response = self.designer_client.get(self.list_url)
        bodies = [c["body"] for c in response.data["results"]]
        self.assertNotIn("Other task comment", bodies)


# ---------------------------------------------------------------------------
# 3. Edit comment
# ---------------------------------------------------------------------------

class CommentUpdateTestCase(CommentFixtureMixin, APITestCase):

    def setUp(self):
        self._setup_fixtures()
        from .models import Comment
        self.comment = Comment.objects.create(
            task=self.task, author=self.designer, body="Original body"
        )
        self.detail_url = comment_detail_url(
            self.slug, self.project_id, self.task_id, self.comment.id
        )

    def test_author_can_edit_own_comment(self):
        response = self.designer_client.patch(self.detail_url, {"body": "Edited body"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["body"], "Edited body")

    def test_non_author_member_cannot_edit_comment(self):
        writer = create_user("writer@x.com")
        from studios.models import StudioMembership
        StudioMembership.objects.create(studio=self.studio, user=writer, role="writer")
        response = auth_client(writer).patch(self.detail_url, {"body": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_edit_others_comment(self):
        # Admin can delete but NOT edit another user's comment
        response = self.admin_client.patch(self.detail_url, {"body": "Admin edit"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_blank_body_on_edit_returns_400(self):
        response = self.designer_client.patch(self.detail_url, {"body": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_edit_comment(self):
        response = APIClient().patch(self.detail_url, {"body": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_edit_updates_updated_at(self):
        original_updated_at = self.comment.updated_at
        self.designer_client.patch(self.detail_url, {"body": "Updated"})
        self.comment.refresh_from_db()
        self.assertGreater(self.comment.updated_at, original_updated_at)

    def test_put_is_not_allowed(self):
        response = self.designer_client.put(self.detail_url, {"body": "Full replace"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ---------------------------------------------------------------------------
# 4. Delete comment
# ---------------------------------------------------------------------------

class CommentDeleteTestCase(CommentFixtureMixin, APITestCase):

    def setUp(self):
        self._setup_fixtures()

    def _make_comment(self, author, body="To be deleted"):
        from .models import Comment
        comment = Comment.objects.create(task=self.task, author=author, body=body)
        return comment_detail_url(self.slug, self.project_id, self.task_id, comment.id)

    def test_author_can_delete_own_comment(self):
        url = self._make_comment(self.designer)
        response = self.designer_client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_admin_can_delete_any_comment(self):
        url = self._make_comment(self.designer)
        response = self.admin_client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_non_author_non_admin_cannot_delete_comment(self):
        writer = create_user("writer2@x.com")
        from studios.models import StudioMembership
        StudioMembership.objects.create(studio=self.studio, user=writer, role="writer")
        url = self._make_comment(self.designer)
        response = auth_client(writer).delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_viewer_cannot_delete_comment(self):
        url = self._make_comment(self.designer)
        response = self.viewer_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_delete_comment(self):
        url = self._make_comment(self.designer)
        response = self.outsider_client.delete(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_delete_comment(self):
        url = self._make_comment(self.designer)
        response = APIClient().delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deleted_comment_no_longer_appears_in_list(self):
        from .models import Comment
        comment = Comment.objects.create(task=self.task, author=self.designer, body="Gone soon")
        detail  = comment_detail_url(self.slug, self.project_id, self.task_id, comment.id)
        self.designer_client.delete(detail)
        response = self.designer_client.get(self.list_url)
        bodies   = [c["body"] for c in response.data["results"]]
        self.assertNotIn("Gone soon", bodies)