from django.urls import path
from .views import (
    PasswordResetView,
    PasswordResetConfirmView,
    ResendVerificationView,
    UserProfilePictureUploadView,
    UserProfilePictureGetView,
    SyncSupabaseUserView,
    SetUserRoleView,
)

urlpatterns = [
    # Password management (server-side Supabase operations)
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "resend-verification/",
        ResendVerificationView.as_view(),
        name="resend_verification",
    ),
    # Profile picture management
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
    # Supabase User Sync — called by Next.js after any successful Supabase auth
    path(
        "auth/sync/",
        SyncSupabaseUserView.as_view(),
        name="supabase_user_sync",
    ),
    # Role finalization — called after Google/One-Tap signup when role is unknown
    path(
        "auth/set-role/",
        SetUserRoleView.as_view(),
        name="set_user_role",
    ),
]
