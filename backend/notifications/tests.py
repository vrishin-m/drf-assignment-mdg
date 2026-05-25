from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Notification

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


def make_notification(recipient, actor=None, event_type=Notification.TASK_ASSIGNED, is_read=False):
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        event_type=event_type,
        payload={"task_title": "Test Task", "project_name": "Test Project", "actor_name": "Admin"},
        is_read=is_read,
    )


NOTIFICATIONS_URL  = reverse("notification-list")
UNREAD_COUNT_URL   = reverse("notification-unread-count")
READ_ALL_URL       = reverse("notification-mark-all-read")


def read_url(notification_id):
    return reverse("notification-mark-read", kwargs={"pk": notification_id})


def detail_url(notification_id):
    return reverse("notification-detail", kwargs={"pk": notification_id})


# ---------------------------------------------------------------------------
# 1. List notifications
# ---------------------------------------------------------------------------

class NotificationListTestCase(APITestCase):

    def setUp(self):
        self.user_a  = create_user("a@x.com")
        self.user_b  = create_user("b@x.com")
        self.actor   = create_user("actor@x.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)

        # 3 notifications for user_a, 1 for user_b
        make_notification(self.user_a, self.actor, Notification.TASK_ASSIGNED)
        make_notification(self.user_a, self.actor, Notification.COMMENT_ADDED)
        make_notification(self.user_a, self.actor, Notification.STAGE_CHANGED)
        make_notification(self.user_b, self.actor, Notification.TASK_ASSIGNED)

    def test_user_sees_only_own_notifications(self):
        response = self.client_a.get(NOTIFICATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_user_b_does_not_see_user_a_notifications(self):
        response = self.client_b.get(NOTIFICATIONS_URL)
        self.assertEqual(response.data["count"], 1)

    def test_notifications_are_ordered_newest_first(self):
        response = self.client_a.get(NOTIFICATIONS_URL)
        results  = response.data["results"]
        # Newest (STAGE_CHANGED) should come first
        self.assertEqual(results[0]["event_type"], Notification.STAGE_CHANGED)

    def test_response_contains_expected_fields(self):
        response = self.client_a.get(NOTIFICATIONS_URL)
        n = response.data["results"][0]
        for field in ["id", "actor", "event_type", "payload", "is_read", "created_at"]:
            self.assertIn(field, n)

    def test_response_does_not_contain_recipient_field(self):
        # recipient is implicitly request.user — no need to expose it
        response = self.client_a.get(NOTIFICATIONS_URL)
        n = response.data["results"][0]
        self.assertNotIn("recipient", n)

    def test_unauthenticated_returns_401(self):
        response = APIClient().get(NOTIFICATIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_is_paginated(self):
        response = self.client_a.get(NOTIFICATIONS_URL)
        self.assertIn("results", response.data)
        self.assertIn("count",   response.data)


# ---------------------------------------------------------------------------
# 2. Single notification retrieve
# ---------------------------------------------------------------------------

class NotificationDetailTestCase(APITestCase):

    def setUp(self):
        self.user_a   = create_user("a@x.com")
        self.user_b   = create_user("b@x.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)
        self.n = make_notification(self.user_a)

    def test_owner_can_retrieve_notification(self):
        response = self.client_a.get(detail_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_retrieve_notification(self):
        response = self.client_b.get(detail_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_retrieve_notification(self):
        response = APIClient().get(detail_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 3. Mark one notification as read
# ---------------------------------------------------------------------------

class MarkReadTestCase(APITestCase):

    def setUp(self):
        self.user_a   = create_user("a@x.com")
        self.user_b   = create_user("b@x.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)
        self.n = make_notification(self.user_a, is_read=False)

    def test_owner_can_mark_notification_read(self):
        response = self.client_a.post(read_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.n.refresh_from_db()
        self.assertTrue(self.n.is_read)

    def test_marking_already_read_notification_is_idempotent(self):
        self.n.is_read = True
        self.n.save()
        response = self.client_a.post(read_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_mark_read(self):
        response = self.client_b.post(read_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.n.refresh_from_db()
        self.assertFalse(self.n.is_read)

    def test_unauthenticated_cannot_mark_read(self):
        response = APIClient().post(read_url(self.n.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_response_contains_updated_is_read_true(self):
        response = self.client_a.post(read_url(self.n.id))
        self.assertTrue(response.data["is_read"])


# ---------------------------------------------------------------------------
# 4. Mark all notifications as read
# ---------------------------------------------------------------------------

class MarkAllReadTestCase(APITestCase):

    def setUp(self):
        self.user_a   = create_user("a@x.com")
        self.user_b   = create_user("b@x.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)

        make_notification(self.user_a, is_read=False)
        make_notification(self.user_a, is_read=False)
        make_notification(self.user_a, is_read=True)   # already read
        make_notification(self.user_b, is_read=False)  # user_b's notification

    def test_marks_all_unread_as_read(self):
        self.client_a.post(READ_ALL_URL)
        unread = Notification.objects.filter(recipient=self.user_a, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_does_not_affect_other_users_notifications(self):
        self.client_a.post(READ_ALL_URL)
        unread_b = Notification.objects.filter(recipient=self.user_b, is_read=False).count()
        self.assertEqual(unread_b, 1)

    def test_response_contains_count_of_marked_notifications(self):
        response = self.client_a.post(READ_ALL_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("marked_read", response.data)
        self.assertEqual(response.data["marked_read"], 2)  # only the 2 unread ones

    def test_calling_again_marks_zero(self):
        self.client_a.post(READ_ALL_URL)
        response = self.client_a.post(READ_ALL_URL)
        self.assertEqual(response.data["marked_read"], 0)

    def test_unauthenticated_returns_401(self):
        response = APIClient().post(READ_ALL_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 5. Unread count
# ---------------------------------------------------------------------------

class UnreadCountTestCase(APITestCase):

    def setUp(self):
        self.user_a   = create_user("a@x.com")
        self.user_b   = create_user("b@x.com")
        self.client_a = auth_client(self.user_a)

        make_notification(self.user_a, is_read=False)
        make_notification(self.user_a, is_read=False)
        make_notification(self.user_a, is_read=True)
        make_notification(self.user_b, is_read=False)

    def test_returns_correct_unread_count(self):
        response = self.client_a.get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_count_decreases_after_marking_read(self):
        n = Notification.objects.filter(recipient=self.user_a, is_read=False).first()
        self.client_a.post(read_url(n.id))
        response = self.client_a.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data["count"], 1)

    def test_count_is_zero_after_mark_all_read(self):
        self.client_a.post(READ_ALL_URL)
        response = self.client_a.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data["count"], 0)

    def test_count_does_not_include_other_users_notifications(self):
        # user_b has 1 unread but user_a's count should still be 2
        response = self.client_a.get(UNREAD_COUNT_URL)
        self.assertEqual(response.data["count"], 2)

    def test_response_shape_is_count_key(self):
        response = self.client_a.get(UNREAD_COUNT_URL)
        self.assertIn("count", response.data)
        self.assertIsInstance(response.data["count"], int)

    def test_unauthenticated_returns_401(self):
        response = APIClient().get(UNREAD_COUNT_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 6. notify() utility
# ---------------------------------------------------------------------------

class NotifyUtilityTestCase(APITestCase):

    def setUp(self):
        self.actor     = create_user("actor@x.com")
        self.recipient = create_user("recipient@x.com")

    def test_notify_creates_notification(self):
        from .utils import notify
        notify(
            recipient=self.recipient,
            actor=self.actor,
            event_type=Notification.TASK_ASSIGNED,
            payload={"task_title": "Do something"},
        )
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 1)

    def test_notify_does_not_self_notify(self):
        from .utils import notify
        notify(
            recipient=self.actor,    # same as actor
            actor=self.actor,
            event_type=Notification.TASK_ASSIGNED,
            payload={},
        )
        self.assertEqual(Notification.objects.filter(recipient=self.actor).count(), 0)

    def test_notify_with_none_recipient_does_nothing(self):
        from .utils import notify
        notify(
            recipient=None,
            actor=self.actor,
            event_type=Notification.TASK_ASSIGNED,
            payload={},
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_notify_with_none_actor_creates_system_notification(self):
        from .utils import notify
        notify(
            recipient=self.recipient,
            actor=None,
            event_type=Notification.TASK_ASSIGNED,
            payload={"task_title": "System task"},
        )
        n = Notification.objects.get(recipient=self.recipient)
        self.assertIsNone(n.actor)

    def test_notify_stage_changed_notifies_assignee_and_lead(self):
        from unittest.mock import MagicMock
        from .utils import notify_stage_changed

        assignee = create_user("assignee@x.com")
        lead     = create_user("lead@x.com")

        task          = MagicMock()
        task.id       = "fake-uuid"
        task.title    = "Mock Task"
        task.assignee = assignee
        task.project.id    = "fake-project"
        task.project.title = "Mock Project"
        task.project.lead  = lead

        notify_stage_changed(task, self.actor, "draft", "review")

        self.assertEqual(Notification.objects.filter(recipient=assignee).count(), 1)
        self.assertEqual(Notification.objects.filter(recipient=lead).count(), 1)

    def test_notify_stage_changed_skips_actor_if_also_assignee(self):
        from unittest.mock import MagicMock
        from .utils import notify_stage_changed

        task          = MagicMock()
        task.id       = "fake-uuid"
        task.title    = "Mock Task"
        task.assignee = self.actor   # actor is also assignee
        task.project.id    = "fake-project"
        task.project.title = "Mock Project"
        task.project.lead  = self.recipient

        notify_stage_changed(task, self.actor, "draft", "review")

        # actor should not receive a notification for their own action
        self.assertEqual(Notification.objects.filter(recipient=self.actor).count(), 0)
        # but the lead should
        self.assertEqual(Notification.objects.filter(recipient=self.recipient).count(), 1)