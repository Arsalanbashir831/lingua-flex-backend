from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    PasswordResetView,
    PasswordResetConfirmView,
    ChangePasswordView,
    TokenRefreshView,
    ResendVerificationView,
    UserProfilePictureUploadView,
    UserProfilePictureGetView,
    GoogleOAuthInitiateView,
    GoogleOAuthCallbackView,
)

urlpatterns = [
    # User Management
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "user/profile-picture/",
        UserProfilePictureUploadView.as_view(),
        name="user_profile_picture_upload",
    ),
    path(
        "user/profile-picture-url/",
        UserProfilePictureGetView.as_view(),
        name="user_profile_picture_get",
    ),
    # Google OAuth Authentication
    path(
        "auth/google/initiate/",
        GoogleOAuthInitiateView.as_view(),
        name="google_oauth_initiate",
    ),
    path(
        "auth/google/callback/",
        GoogleOAuthCallbackView.as_view(),
        name="google_oauth_callback",
    ),
]
