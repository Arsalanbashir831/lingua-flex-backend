from django.urls import path
from .views import (
    UserProfilePictureUploadView,
    UserProfilePictureGetView,
    SyncSupabaseUserView,
    SetUserRoleView,
    HealthCheckView,
)

urlpatterns = [
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
    # CI/CD health-check and uptime monitoring endpoint (no auth required)
    path(
        "health/",
        HealthCheckView.as_view(),
        name="health_check",
    ),
]
