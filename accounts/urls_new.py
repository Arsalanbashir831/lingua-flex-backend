# accounts/urls_new.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_new import (
    LanguageViewSet,
    SimpleRegistrationView,
    UserProfileViewSet,
    TeacherProfileViewSet,
    ChatViewSet,
    MessageViewSet,
    GigViewSet,
    supabase_chats,
    supabase_messages,
)

router = DefaultRouter()
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'teachers', TeacherProfileViewSet, basename='teacher')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'gigs', GigViewSet, basename='gig')

urlpatterns = [
    path('', include(router.urls)),
    
    # Simplified registration
    path('register/', SimpleRegistrationView.as_view(), name='simple-register'),
    
    # Profile management endpoints
    path('profile/me/', UserProfileViewSet.as_view({'get': 'me'}), name='my-profile'),
    path('profile/update-student/', UserProfileViewSet.as_view({'put': 'update_student_profile', 'patch': 'update_student_profile'}), name='update-student-profile'),
    
    # Teacher-specific endpoints
    path('teacher/me/', TeacherProfileViewSet.as_view({'get': 'me'}), name='my-teacher-profile'),
    path('teacher/update/', TeacherProfileViewSet.as_view({'put': 'update_teacher_profile', 'patch': 'update_teacher_profile'}), name='update-teacher-profile'),
    path('teacher/list/', TeacherProfileViewSet.as_view({'get': 'list_teachers'}), name='list-teachers'),
    
    # Chat endpoints (Supabase integration)
    path('supabase/chats/', supabase_chats, name='supabase-chats'),
    path('supabase/messages/<uuid:chat_id>/', supabase_messages, name='supabase-messages'),
]
