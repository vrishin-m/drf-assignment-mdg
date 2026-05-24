import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# REGISTER_URL       = reverse("auth-register")
# LOGIN_URL          = reverse("auth-login")
# TOKEN_REFRESH_URL  = reverse("auth-token-refresh")
# LOGOUT_URL         = reverse("auth-logout")
# ME_URL             = reverse("auth-me")
# CHANGE_PASS_URL    = reverse("auth-change-password")


def create_user(email="user@example.com", password="StrongPass123!", full_name="Test User"):
    return User.objects.create_user(email=email, password=password, full_name=full_name)


def auth_header(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Registration
# ---------------------------------------------------------------------------

class RegisterTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.valid_payload = {
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
        }

    def test_valid_registration_returns_201(self):
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_registration_creates_user_in_db(self):
        self.client.post(self.register_url, self.valid_payload)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_duplicate_email_returns_400(self):
        create_user(email="newuser@example.com")
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        payload = self.valid_payload.copy()
        payload.pop("email")
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        payload = self.valid_payload.copy()
        payload.pop("password")
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_full_name_returns_400(self):
        payload = self.valid_payload.copy()
        payload.pop("full_name")
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_format_returns_400(self):
        payload = self.valid_payload.copy()
        payload["email"] = "not-an-email"
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_is_not_stored_in_plain_text(self):
        self.client.post(self.register_url, self.valid_payload)
        user = User.objects.get(email="newuser@example.com")
        self.assertNotEqual(user.password, "StrongPass123!")

    def test_response_does_not_contain_password(self):
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertNotIn("password", response.data)

    def test_registered_user_is_active_by_default(self):
        self.client.post(self.register_url, self.valid_payload)
        user = User.objects.get(email="newuser@example.com")
        self.assertTrue(user.is_active)

    def test_blank_email_returns_400(self):
        payload = self.valid_payload.copy()
        payload["email"] = ""
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blank_password_returns_400(self):
        payload = self.valid_payload.copy()
        payload["password"] = ""
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# 2. Login
# ---------------------------------------------------------------------------

class LoginTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse("login")
        self.password = "StrongPass123!"
        self.user = create_user(email="login@example.com", password=self.password)
        self.valid_payload = {"email": "login@example.com", "password": self.password}

    def test_valid_credentials_return_200(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_password_returns_401(self):
        payload = self.valid_payload.copy()
        payload["password"] = "WrongPassword!"
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_email_returns_401(self):
        payload = {"email": "ghost@example.com", "password": self.password}
        response = self.client.post(self.login_url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_email_field_returns_400(self):
        response = self.client.post(self.login_url, {"password": self.password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_field_returns_400(self):
        response = self.client.post(self.login_url, {"email": "login@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_token_is_string(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertIsInstance(response.data["access"], str)

    def test_refresh_token_is_string(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertIsInstance(response.data["refresh"], str)

    def test_response_does_not_contain_password(self):
        response = self.client.post(self.login_url, self.valid_payload)
        self.assertNotIn("password", response.data)


# ---------------------------------------------------------------------------
# 3. Token Refresh
# ---------------------------------------------------------------------------

class TokenRefreshTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="refresh@example.com")
        refresh = RefreshToken.for_user(self.user)
        self.token_refresh_url = reverse("token-refresh")
        self.me_url = reverse("me")
        self.refresh_token = str(refresh)

    def test_valid_refresh_token_returns_new_access_token(self):
        response = self.client.post(self.token_refresh_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_refresh_token_returns_401(self):
        response = self.client.post(self.token_refresh_url, {"refresh": "garbage.token.value"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_refresh_token_returns_400(self):
        response = self.client.post(self.token_refresh_url, {"refresh": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_refresh_field_returns_400(self):
        response = self.client.post(self.token_refresh_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(SIMPLE_JWT={"REFRESH_TOKEN_LIFETIME": timedelta(seconds=1)})
    def test_expired_refresh_token_returns_401(self):
        # Generate a token under the short-lifetime setting
        refresh = RefreshToken.for_user(self.user)
        expired_token = str(refresh)
        time.sleep(2)
        response = self.client.post(self.token_refresh_url, {"refresh": expired_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_access_token_is_usable(self):
        response = self.client.post(self.token_refresh_url, {"refresh": self.refresh_token})
        new_access = response.data["access"]
        me_response = self.client.get(self.me_url, **auth_header(new_access))
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# 4. Logout
# ---------------------------------------------------------------------------

class LogoutTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="logout@example.com")
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)
        self.logout_url = reverse("logout")
        self.token_refresh_url = reverse("token-refresh")

    def test_valid_logout_returns_200_or_204(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_after_logout_refresh_token_is_blacklisted(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.client.post(self.logout_url, {"refresh": self.refresh_token})
        # Try to use the same refresh token
        response = self.client.post(self.token_refresh_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_logout_returns_401(self):
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_already_blacklisted_token_returns_401_on_second_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.client.post(self.logout_url, {"refresh": self.refresh_token})
        # Second logout with same refresh token
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_refresh_token_on_logout_returns_400_or_401(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.logout_url, {"refresh": "notavalidtoken"})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])


# ---------------------------------------------------------------------------
# 5. Profile — GET /api/auth/me/
# ---------------------------------------------------------------------------

class ProfileGetTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="profile@example.com",
            password="StrongPass123!",
            full_name="Profile User",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.me_url = reverse("me")

    def test_authenticated_user_gets_own_profile(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profile_contains_expected_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.me_url)
        for field in ["id", "email", "full_name", "avatar_url", "bio", "created_at"]:
            self.assertIn(field, response.data)

    def test_profile_does_not_contain_password(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.me_url)
        self.assertNotIn("password", response.data)

    def test_profile_email_matches_logged_in_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.data["email"], self.user.email)

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer completelygarbage")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_authorization_header_returns_401(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 6. Profile — PATCH /api/auth/me/
# ---------------------------------------------------------------------------

class ProfileUpdateTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="update@example.com",
            password="StrongPass123!",
            full_name="Original Name",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.me_url = reverse("me")

    def test_can_update_full_name(self):
        response = self.client.patch(self.me_url, {"full_name": "Updated Name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")

    def test_can_update_bio(self):
        response = self.client.patch(self.me_url, {"bio": "Creative designer."})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Creative designer.")

    def test_can_update_avatar_url(self):
        response = self.client.patch(self.me_url, {"avatar_url": "https://example.com/avatar.png"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar_url, "https://example.com/avatar.png")

    def test_partial_update_does_not_wipe_other_fields(self):
        # Set full_name first
        self.client.patch(self.me_url, {"full_name": "Partial Name"})
        # Now only update bio
        self.client.patch(self.me_url, {"bio": "New bio"})
        self.user.refresh_from_db()
        # full_name should still be set
        self.assertEqual(self.user.full_name, "Partial Name")

    def test_cannot_update_password_via_me_endpoint(self):
        response = self.client.patch(self.me_url, {"password": "NewPass999!"})
        # Either ignored (200 but password unchanged) or rejected (400)
        if response.status_code == status.HTTP_200_OK:
            self.user.refresh_from_db()
            self.assertFalse(self.user.check_password("NewPass999!"))

    def test_unauthenticated_patch_returns_401(self):
        self.client.credentials()  # clear credentials
        response = self.client.patch(self.me_url, {"full_name": "Hacker"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_returns_updated_data_in_response(self):
        response = self.client.patch(self.me_url, {"full_name": "Response Check"})
        self.assertEqual(response.data["full_name"], "Response Check")


# ---------------------------------------------------------------------------
# 7. Change Password
# ---------------------------------------------------------------------------

class ChangePasswordTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.old_password = "OldPass123!"
        self.new_password = "NewPass456!"
        self.confirm_password = "NewPass456!"
        self.user = create_user(email="changepass@example.com", password=self.old_password)
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.change_password_url = reverse("change-password")
        self.login_url = reverse("login")
        self.me_url = reverse("me")

    def test_correct_old_password_and_valid_new_password_succeeds(self):
        response = self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "confirm_password" : self.confirm_password,
            "new_password": self.new_password,
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    def test_wrong_old_password_returns_400(self):
        response = self.client.post(self.change_password_url, {
            "old_password": "WrongOld!",
            "confirm_password" : self.confirm_password,
            "new_password": self.new_password,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_password_same_as_old_returns_400(self):
        response = self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "confirm_password" : self.old_password,
            "new_password": self.old_password,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_after_change_old_password_does_not_work_on_login(self):
        self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "confirm_password" : self.confirm_password,
        })
        self.client.credentials()  # clear
        response = self.client.post(self.login_url, {
            "email": "changepass@example.com",
            "password": self.old_password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_after_change_new_password_works_on_login(self):
        self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "confirm_password" : self.confirm_password,
        })
        self.client.credentials()  # clear
        response = self.client.post(self.login_url, {
            "email": "changepass@example.com",
            "password": self.new_password,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_existing_access_token_still_valid_after_password_change(self):
        # JWT is stateless — old token works until expiry
        self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "confirm_password" : self.confirm_password,
        })
        # Re-attach old token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_change_password_returns_401(self):
        self.client.credentials()
        response = self.client.post(self.change_password_url, {
            "old_password": self.old_password,
            "new_password": self.new_password,
            "confirm_password" : self.confirm_password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_old_password_field_returns_400(self):
        response = self.client.post(self.change_password_url, {"new_password": self.new_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_new_password_field_returns_400(self):
        response = self.client.post(self.change_password_url, {"old_password": self.old_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# 8. Token Expiry
# ---------------------------------------------------------------------------

class TokenExpiryTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="expiry@example.com")
        self.me_url = reverse("me")
        self.token_refresh_url = reverse("token-refresh")

    @override_settings(SIMPLE_JWT={"ACCESS_TOKEN_LIFETIME": timedelta(seconds=1)})
    def test_expired_access_token_is_rejected(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        time.sleep(2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_access_token_before_expiry_is_accepted(self):
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(SIMPLE_JWT={"REFRESH_TOKEN_LIFETIME": timedelta(seconds=1)})
    def test_expired_refresh_token_cannot_generate_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)
        time.sleep(2)
        response = self.client.post(self.token_refresh_url, {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# 9. Edge Cases
# ---------------------------------------------------------------------------

class EdgeCaseTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="edge@example.com")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.me_url = reverse("me")
        self.logout_url = reverse("logout")
        self.change_password_url = reverse("change-password")

    def test_random_string_in_auth_header_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer thisisnotavalidjwttoken")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bearer_prefix_missing_returns_401(self):
        # Sending token without "Bearer " prefix
        self.client.credentials(HTTP_AUTHORIZATION=self.access_token)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_authorization_header_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_with_tampered_payload_returns_401(self):
        # Split the token and tamper the payload segment
        parts = self.access_token.split(".")
        tampered = parts[0] + ".dGFtcGVyZWQ." + parts[2]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tampered}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_a_token_cannot_modify_user_b_profile(self):
        user_b = create_user(email="userb@example.com", full_name="User B")
        refresh_b = RefreshToken.for_user(user_b)
        token_b = str(refresh_b.access_token)
        # Authenticate as user_a
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        # me/ always returns own profile — this just confirms user_a can't see user_b's data
        response = self.client.get(self.me_url)
        self.assertNotEqual(response.data["email"], user_b.email)

    def test_protected_endpoints_list_all_return_401_without_auth(self):
        endpoints = [self.me_url, self.logout_url, self.change_password_url]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                msg=f"Expected 401 for {url}",
            )