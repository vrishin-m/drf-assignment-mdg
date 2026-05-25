from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(email="user@example.com", password="StrongPass123!", full_name="Test User"):
    return User.objects.create_user(email=email, password=password, full_name=full_name)


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def auth_client(user):
    """Return an APIClient already authenticated for the given user."""
    client = APIClient()
    access, _ = get_tokens(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


# URL helpers — adjust names to match your urls.py
STUDIOS_LIST_URL    = reverse("studio-list")          # GET list / POST create


def studio_detail_url(slug):
    return reverse("studio-detail", kwargs={"slug": slug})


def studio_members_url(slug):
    return reverse("studio-member-list", kwargs={"slug": slug})


def studio_member_detail_url(slug, user_id):
    return reverse("studio-member-detail", kwargs={"slug": slug, "user_id": user_id})


def my_membership_url(slug):
    return reverse("studio-my-membership", kwargs={"slug": slug})


# ---------------------------------------------------------------------------
# 1. Studio CRUD
# ---------------------------------------------------------------------------

class StudioCreateTestCase(APITestCase):

    def setUp(self):
        self.user = create_user(email="creator@example.com")
        self.client = auth_client(self.user)
        self.valid_payload = {
            "name": "Pixel Studio",
            "slug": "pixel-studio",
        }

    def test_authenticated_user_can_create_studio(self):
        response = self.client.post(STUDIOS_LIST_URL, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_user_cannot_create_studio(self):
        client = APIClient()
        response = client.post(STUDIOS_LIST_URL, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creator_is_automatically_made_studio_admin(self):
        self.client.post(STUDIOS_LIST_URL, self.valid_payload)
        # Check own membership
        response = self.client.get(my_membership_url("pixel-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "studio_admin")

    def test_missing_name_returns_400(self):
        payload = self.valid_payload.copy()
        payload.pop("name")
        response = self.client.post(STUDIOS_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_slug_returns_400(self):
        payload = self.valid_payload.copy()
        payload.pop("slug")
        response = self.client.post(STUDIOS_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_slug_returns_400(self):
        self.client.post(STUDIOS_LIST_URL, self.valid_payload)
        other_user = create_user(email="other@example.com")
        other_client = auth_client(other_user)
        response = other_client.post(STUDIOS_LIST_URL, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_created_studio_appears_in_response(self):
        response = self.client.post(STUDIOS_LIST_URL, self.valid_payload)
        self.assertEqual(response.data["slug"], "pixel-studio")
        self.assertEqual(response.data["name"], "Pixel Studio")

    def test_blank_name_returns_400(self):
        payload = self.valid_payload.copy()
        payload["name"] = ""
        response = self.client.post(STUDIOS_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_slug_returns_400(self):
        payload = self.valid_payload.copy()
        payload["slug"] = ""
        response = self.client.post(STUDIOS_LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StudioListTestCase(APITestCase):

    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)

        # user_a creates two studios
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Studio A1", "slug": "studio-a1"})
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Studio A2", "slug": "studio-a2"})
        # user_b creates one studio
        self.client_b.post(STUDIOS_LIST_URL, {"name": "Studio B1", "slug": "studio-b1"})

    def test_user_sees_only_their_own_studios(self):
        response = self.client_a.get(STUDIOS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [s["slug"] for s in response.data]
        self.assertIn("studio-a1", slugs)
        self.assertIn("studio-a2", slugs)
        self.assertNotIn("studio-b1", slugs)

    def test_unauthenticated_list_returns_401(self):
        client = APIClient()
        response = client.get(STUDIOS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_with_no_studios_gets_empty_list(self):
        new_user = create_user(email="nobody@example.com")
        client = auth_client(new_user)
        response = client.get(STUDIOS_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class StudioDetailTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.member = create_user(email="member@example.com")
        self.outsider = create_user(email="outsider@example.com")

        self.admin_client = auth_client(self.admin)
        self.member_client = auth_client(self.member)
        self.outsider_client = auth_client(self.outsider)

        # Admin creates studio
        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Detail Studio", "slug": "detail-studio"})

        # Add member as designer
        self.admin_client.post(
            studio_members_url("detail-studio"),
            {"user": self.member.id, "role": "designer"},
        )

    def test_admin_can_retrieve_studio(self):
        response = self.admin_client.get(studio_detail_url("detail-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_can_retrieve_studio(self):
        response = self.member_client.get(studio_detail_url("detail-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_member_cannot_retrieve_studio(self):
        response = self.outsider_client.get(studio_detail_url("detail-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_retrieve_studio(self):
        client = APIClient()
        response = client.get(studio_detail_url("detail-studio"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_detail_response_contains_expected_fields(self):
        response = self.admin_client.get(studio_detail_url("detail-studio"))
        for field in ["id", "name", "slug", "created_at"]:
            self.assertIn(field, response.data)

    def test_nonexistent_studio_returns_404(self):
        response = self.admin_client.get(studio_detail_url("does-not-exist"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StudioUpdateTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.designer = create_user(email="designer@example.com")

        self.admin_client = auth_client(self.admin)
        self.designer_client = auth_client(self.designer)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Update Studio", "slug": "update-studio"})
        self.admin_client.post(
            studio_members_url("update-studio"),
            {"user": self.designer.id, "role": "designer"},
        )

    def test_admin_can_update_studio_name(self):
        response = self.admin_client.patch(
            studio_detail_url("update-studio"), {"name": "Renamed Studio"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Renamed Studio")

    def test_admin_can_update_logo_url(self):
        response = self.admin_client.patch(
            studio_detail_url("update-studio"), {"logo_url": "https://example.com/logo.png"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_member_cannot_update_studio(self):
        response = self.designer_client.patch(
            studio_detail_url("update-studio"), {"name": "Hacked Name"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_update_studio(self):
        outsider = create_user(email="outsider@example.com")
        outsider_client = auth_client(outsider)
        response = outsider_client.patch(
            studio_detail_url("update-studio"), {"name": "Hacked"}
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_update_studio(self):
        client = APIClient()
        response = client.patch(studio_detail_url("update-studio"), {"name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StudioDeleteTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.designer = create_user(email="designer@example.com")

        self.admin_client = auth_client(self.admin)
        self.designer_client = auth_client(self.designer)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Delete Studio", "slug": "delete-studio"})
        self.admin_client.post(
            studio_members_url("delete-studio"),
            {"user": self.designer.id, "role": "designer"},
        )

    def test_non_admin_cannot_delete_studio(self):
        response = self.designer_client.delete(studio_detail_url("delete-studio"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_delete_studio(self):
        outsider = create_user(email="outsider@example.com")
        outsider_client = auth_client(outsider)
        response = outsider_client.delete(studio_detail_url("delete-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_admin_can_delete_studio(self):
        response = self.admin_client.delete(studio_detail_url("delete-studio"))
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_after_deletion_studio_is_not_accessible(self):
        self.admin_client.delete(studio_detail_url("delete-studio"))
        response = self.admin_client.get(studio_detail_url("delete-studio"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_after_deletion_memberships_are_gone(self):
        from studios.models import StudioMembership  # adjust import to your app
        self.admin_client.delete(studio_detail_url("delete-studio"))
        # No memberships should remain for this studio slug
        exists = StudioMembership.objects.filter(studio__slug="delete-studio").exists()
        self.assertFalse(exists)

    def test_unauthenticated_cannot_delete_studio(self):
        client = APIClient()
        response = client.delete(studio_detail_url("delete-studio"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 2. Studio Membership Management
# ---------------------------------------------------------------------------

class MemberInviteTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.invitee = create_user(email="invitee@example.com")

        self.admin_client = auth_client(self.admin)
        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Invite Studio", "slug": "invite-studio"})

    def test_admin_can_invite_user_with_role(self):
        response = self.admin_client.post(
            studio_members_url("invite-studio"),
            {"user": self.invitee.id, "role": "designer"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invited_member_role_is_correct(self):
        self.admin_client.post(
            studio_members_url("invite-studio"),
            {"user": self.invitee.id, "role": "designer"},
        )
        response = auth_client(self.invitee).get(my_membership_url("invite-studio"))
        self.assertEqual(response.data["role"], "designer")

    def test_inviting_nonexistent_user_returns_400_or_404(self):
        response = self.admin_client.post(
            studio_members_url("invite-studio"),
            {"user": "00000000-0000-0000-0000-000000000000", "role": "designer"},
        )
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_inviting_with_invalid_role_returns_400(self):
        response = self.admin_client.post(
            studio_members_url("invite-studio"),
            {"user": self.invitee.id, "role": "overlord"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admin_cannot_invite_members(self):
        designer = create_user(email="designer@example.com")
        self.admin_client.post(
            studio_members_url("invite-studio"),
            {"user": designer.id, "role": "designer"},
        )
        outsider = create_user(email="outsider@example.com")
        designer_client = auth_client(designer)
        response = designer_client.post(
            studio_members_url("invite-studio"),
            {"user": outsider.id, "role": "writer"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_cannot_invite_members(self):
        outsider = create_user(email="outsider@example.com")
        outsider_client = auth_client(outsider)
        response = outsider_client.post(
            studio_members_url("invite-studio"),
            {"user": self.invitee.id, "role": "designer"},
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_invite_members(self):
        client = APIClient()
        response = client.post(
            studio_members_url("invite-studio"),
            {"user": self.invitee.id, "role": "designer"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_all_valid_roles_can_be_assigned(self):
        valid_roles = ["project_lead", "designer", "writer", "reviewer", "client_viewer"]
        users = [create_user(email=f"role_{r}@example.com") for r in valid_roles]
        for user, role in zip(users, valid_roles):
            response = self.admin_client.post(
                studio_members_url("invite-studio"),
                {"user": user.id, "role": role},
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                msg=f"Role '{role}' should be assignable",
            )


class MemberListTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.member = create_user(email="member@example.com")
        self.outsider = create_user(email="outsider@example.com")

        self.admin_client = auth_client(self.admin)
        self.member_client = auth_client(self.member)
        self.outsider_client = auth_client(self.outsider)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "List Studio", "slug": "list-studio"})
        self.admin_client.post(
            studio_members_url("list-studio"),
            {"user": self.member.id, "role": "designer"},
        )

    def test_admin_can_list_members(self):
        response = self.admin_client.get(studio_members_url("list-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_can_list_members(self):
        response = self.member_client.get(studio_members_url("list-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_list_includes_all_members(self):
        response = self.admin_client.get(studio_members_url("list-studio"))
        emails = [m["user"]["email"] for m in response.data]
        self.assertIn("admin@example.com", emails)
        self.assertIn("member@example.com", emails)

    def test_member_list_includes_role_field(self):
        response = self.admin_client.get(studio_members_url("list-studio"))
        for member in response.data:
            self.assertIn("role", member)

    def test_outsider_cannot_list_members(self):
        response = self.outsider_client.get(studio_members_url("list-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_cannot_list_members(self):
        client = APIClient()
        response = client.get(studio_members_url("list-studio"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_viewer_can_list_members_but_not_manage(self):
        viewer = create_user(email="viewer@example.com")
        self.admin_client.post(
            studio_members_url("list-studio"),
            {"user": viewer.id, "role": "client_viewer"},
        )
        viewer_client = auth_client(viewer)
        # Can list
        response = viewer_client.get(studio_members_url("list-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Cannot invite
        new_user = create_user(email="new@example.com")
        response = viewer_client.post(
            studio_members_url("list-studio"),
            {"user": new_user.id, "role": "writer"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MemberUpdateTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.designer = create_user(email="designer@example.com")
        self.other_admin = create_user(email="admin2@example.com")

        self.admin_client = auth_client(self.admin)
        self.designer_client = auth_client(self.designer)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Update Member Studio", "slug": "update-member-studio"})
        self.admin_client.post(
            studio_members_url("update-member-studio"),
            {"user": self.designer.id, "role": "designer"},
        )

    def test_admin_can_update_member_role(self):
        response = self.admin_client.patch(
            studio_member_detail_url("update-member-studio", self.designer.id),
            {"role": "writer"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "writer")

    def test_non_admin_cannot_update_member_role(self):
        other = create_user(email="other@example.com")
        self.admin_client.post(
            studio_members_url("update-member-studio"),
            {"user": other.id, "role": "writer"},
        )
        response = self.designer_client.patch(
            studio_member_detail_url("update-member-studio", other.id),
            {"role": "reviewer"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_updating_to_invalid_role_returns_400(self):
        response = self.admin_client.patch(
            studio_member_detail_url("update-member-studio", self.designer.id),
            {"role": "god_mode"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_demote_themselves_if_only_admin(self):
        # Only one admin exists — demoting should fail
        response = self.admin_client.patch(
            studio_member_detail_url("update-member-studio", self.admin.id),
            {"role": "designer"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_demote_themselves_if_another_admin_exists(self):
        # Promote designer to admin first
        self.admin_client.patch(
            studio_member_detail_url("update-member-studio", self.designer.id),
            {"role": "studio_admin"},
        )
        # Now the original admin can safely demote themselves
        response = self.admin_client.patch(
            studio_member_detail_url("update-member-studio", self.admin.id),
            {"role": "designer"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MemberRemoveTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.designer = create_user(email="designer@example.com")

        self.admin_client = auth_client(self.admin)
        self.designer_client = auth_client(self.designer)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "Remove Studio", "slug": "remove-studio"})
        self.admin_client.post(
            studio_members_url("remove-studio"),
            {"user": self.designer.id, "role": "designer"},
        )

    def test_admin_can_remove_a_member(self):
        response = self.admin_client.delete(
            studio_member_detail_url("remove-studio", self.designer.id)
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_after_removal_member_cannot_access_studio(self):
        self.admin_client.delete(
            studio_member_detail_url("remove-studio", self.designer.id)
        )
        response = self.designer_client.get(studio_detail_url("remove-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_non_admin_cannot_remove_member(self):
        writer = create_user(email="writer@example.com")
        self.admin_client.post(
            studio_members_url("remove-studio"),
            {"user": writer.id, "role": "writer"},
        )
        response = self.designer_client.delete(
            studio_member_detail_url("remove-studio", writer.id)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_remove_themselves_if_only_admin(self):
        response = self.admin_client.delete(
            studio_member_detail_url("remove-studio", self.admin.id)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_remove_member(self):
        outsider = create_user(email="outsider@example.com")
        outsider_client = auth_client(outsider)
        response = outsider_client.delete(
            studio_member_detail_url("remove-studio", self.designer.id)
        )
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_removing_nonexistent_member_returns_404(self):
        ghost = create_user(email="ghost@example.com")
        response = self.admin_client.delete(
            studio_member_detail_url("remove-studio", ghost.id)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# 3. My Membership — /api/studios/{slug}/members/me/
# ---------------------------------------------------------------------------

class MyMembershipTestCase(APITestCase):

    def setUp(self):
        self.admin = create_user(email="admin@example.com")
        self.reviewer = create_user(email="reviewer@example.com")
        self.outsider = create_user(email="outsider@example.com")

        self.admin_client = auth_client(self.admin)
        self.reviewer_client = auth_client(self.reviewer)
        self.outsider_client = auth_client(self.outsider)

        self.admin_client.post(STUDIOS_LIST_URL, {"name": "My Studio", "slug": "my-studio"})
        self.admin_client.post(
            studio_members_url("my-studio"),
            {"user": self.reviewer.id, "role": "reviewer"},
        )

    def test_member_can_get_own_membership(self):
        response = self.reviewer_client.get(my_membership_url("my-studio"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_membership_includes_role(self):
        response = self.reviewer_client.get(my_membership_url("my-studio"))
        self.assertIn("role", response.data)
        self.assertEqual(response.data["role"], "reviewer")

    def test_my_membership_includes_joined_at(self):
        response = self.reviewer_client.get(my_membership_url("my-studio"))
        self.assertIn("joined_at", response.data)

    def test_my_membership_includes_user_info(self):
        response = self.reviewer_client.get(my_membership_url("my-studio"))
        self.assertIn("user", response.data)

    def test_non_member_gets_403_or_404(self):
        response = self.outsider_client.get(my_membership_url("my-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_unauthenticated_gets_401(self):
        client = APIClient()
        response = client.get(my_membership_url("my-studio"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_my_membership_shows_studio_admin_role(self):
        response = self.admin_client.get(my_membership_url("my-studio"))
        self.assertEqual(response.data["role"], "studio_admin")


# ---------------------------------------------------------------------------
# 4. Edge Cases
# ---------------------------------------------------------------------------

class StudioEdgeCaseTestCase(APITestCase):

    def setUp(self):
        self.user_a = create_user(email="a@example.com")
        self.user_b = create_user(email="b@example.com")
        self.client_a = auth_client(self.user_a)
        self.client_b = auth_client(self.user_b)

    def test_user_can_be_member_of_multiple_studios_with_different_roles(self):
        # user_a creates two studios and invites user_b with different roles
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Studio One", "slug": "studio-one"})
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Studio Two", "slug": "studio-two"})

        self.client_a.post(
            studio_members_url("studio-one"),
            {"user": self.user_b.id, "role": "designer"},
        )
        self.client_a.post(
            studio_members_url("studio-two"),
            {"user": self.user_b.id, "role": "reviewer"},
        )

        r1 = self.client_b.get(my_membership_url("studio-one"))
        r2 = self.client_b.get(my_membership_url("studio-two"))

        self.assertEqual(r1.data["role"], "designer")
        self.assertEqual(r2.data["role"], "reviewer")

    def test_slug_is_unique_across_system(self):
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Slug Studio", "slug": "unique-slug"})
        # user_b tries same slug
        response = self.client_b.post(STUDIOS_LIST_URL, {"name": "Other Studio", "slug": "unique-slug"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_removed_member_studio_no_longer_appears_in_their_list(self):
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Temp Studio", "slug": "temp-studio"})
        self.client_a.post(
            studio_members_url("temp-studio"),
            {"user": self.user_b.id, "role": "writer"},
        )
        # Confirm user_b sees it
        response = self.client_b.get(STUDIOS_LIST_URL)
        slugs = [s["slug"] for s in response.data]
        self.assertIn("temp-studio", slugs)

        # Admin removes user_b
        self.client_a.delete(studio_member_detail_url("temp-studio", self.user_b.id))

        # user_b no longer sees it
        response = self.client_b.get(STUDIOS_LIST_URL)
        slugs = [s["slug"] for s in response.data]
        self.assertNotIn("temp-studio", slugs)

    def test_user_b_studio_not_visible_to_user_a_who_is_not_member(self):
        self.client_b.post(STUDIOS_LIST_URL, {"name": "Private Studio", "slug": "private-studio"})
        response = self.client_a.get(studio_detail_url("private-studio"))
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_promoting_member_to_studio_admin_gives_admin_privileges(self):
        self.client_a.post(STUDIOS_LIST_URL, {"name": "Promote Studio", "slug": "promote-studio"})
        self.client_a.post(
            studio_members_url("promote-studio"),
            {"user": self.user_b.id, "role": "designer"},
        )
        # Promote user_b to studio_admin
        self.client_a.patch(
            studio_member_detail_url("promote-studio", self.user_b.id),
            {"role": "studio_admin"},
        )
        # user_b should now be able to invite someone
        new_user = create_user(email="new@example.com")
        response = self.client_b.post(
            studio_members_url("promote-studio"),
            {"user": new_user.id, "role": "writer"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)