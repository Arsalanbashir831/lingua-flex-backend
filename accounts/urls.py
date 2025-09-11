from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LanguageViewSet,
    RegisterWithProfileView,
    UserProfileViewSet,
    TeacherProfileViewSet,
    ChatViewSet,
    MessageViewSet,
    GigViewSet,
    VoiceConversationViewSet,
    supabase_chats,
    supabase_messages,
)

router = DefaultRouter()
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'teachers', TeacherProfileViewSet, basename='teacher')
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'gigs', GigViewSet, basename='gig')
router.register(r'voice-conversations', VoiceConversationViewSet, basename='voice-conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterWithProfileView.as_view(), name='register-with-profile'),
    path('supabase/chats/', supabase_chats, name='supabase-chats'),
    path('supabase/messages/<uuid:chat_id>/', supabase_messages, name='supabase-messages'),
    # Include student management endpoints for teachers
    path('', include('accounts.urls_students')),
]
