from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .views import (
    RegisterView,
    MeView,
    ChangePasswordView,
    LogoutView,
    LoginView,

)


urlpatterns = [

    # Authentication
    path(
        "auth/register/",
        RegisterView.as_view(),
        name="register"
    ),

    path(
        "auth/login/",
        LoginView.as_view(),
        name="login"
    ),

    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh"
    ),

    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="logout"
    ),

    # User profile
    path(
        "auth/me/",
        MeView.as_view(),
        name="me"
    ),

    path(
        "auth/me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password"
    ),
]