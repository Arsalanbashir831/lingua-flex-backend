from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterWithProfileView,
    UserProfileViewSet,
    TeacherProfileViewSet,
    GigViewSet,
    VoiceConversationViewSet,
    supabase_chats,
    become_teacher,
    become_student,
    roles_status,
)

router = DefaultRouter()
router.register(r"profiles", UserProfileViewSet, basename="profile")
router.register(r"teachers", TeacherProfileViewSet, basename="teacher")
router.register(r"gigs", GigViewSet, basename="gig")
router.register(
    r"voice-conversations", VoiceConversationViewSet, basename="voice-conversation"
)

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterWithProfileView.as_view(), name="register-with-profile"),
    # New role management endpoints
    path("become-teacher/", become_teacher, name="become-teacher"),
    path("become-student/", become_student, name="become-student"),
    # Combined roles status endpoint for the authenticated user's profiles
    path("profiles/me/roles/", roles_status, name="profiles-me-roles"),
    path("supabase/chats/", supabase_chats, name="supabase-chats"),
]
