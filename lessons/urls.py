from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VoiceAvatarViewSet,
    LearningContextViewSet,
    AISessionViewSet,
    LearningProgressViewSet,
)

router = DefaultRouter()
router.register(r'voice-avatars', VoiceAvatarViewSet, basename='voice-avatar')
router.register(r'contexts', LearningContextViewSet, basename='context')
router.register(r'sessions', AISessionViewSet, basename='session')
router.register(r'progress', LearningProgressViewSet, basename='progress')

urlpatterns = [
    path('', include(router.urls)),
]
