from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Avg
from .models import (
    VoiceAvatar, LearningContext, AISession,
    Conversation, LearningProgress
)
from .serializers import (
    VoiceAvatarSerializer, LearningContextSerializer,
    AISessionSerializer, AISessionCreateSerializer,
    ConversationSerializer, LearningProgressSerializer
)
# TODO: Re-enable Hume integration once we have the correct SDK version
# from hume import HumeApi
# from hume.source import Source
from django.conf import settings
import asyncio

class VoiceAvatarViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VoiceAvatar.objects.filter(is_active=True)
    serializer_class = VoiceAvatarSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        language = self.request.query_params.get('language', None)
        if language:
            queryset = queryset.filter(language__code=language)
        return queryset

class LearningContextViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LearningContext.objects.filter(is_active=True)
    serializer_class = LearningContextSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        difficulty = self.request.query_params.get('difficulty', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        return queryset

class AISessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AISessionCreateSerializer
        return AISessionSerializer
    
    def get_queryset(self):
        return AISession.objects.filter(student__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user.profile)
    
    @action(detail=True, methods=['post'])
    async def process_conversation(self, request, pk=None):
        session = self.get_object()
        user_input = request.data.get('user_input')
        audio_file = request.data.get('audio_file')
        
        if not user_input or not audio_file:
            return Response(
                {'error': 'Both user_input and audio_file are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # TODO: Re-enable Hume AI integration
            # Temporarily return mock emotion data
            emotions = {"mock": "emotions"}
            
            # Generate AI response using context and emotions
            ai_response = self._generate_ai_response(
                session.context,
                user_input,
                emotions
            )
            
            # Create conversation record
            conversation = Conversation.objects.create(
                session=session,
                user_input=user_input,
                ai_response=ai_response,
                user_audio_url=audio_file.url,
                emotion_metrics=emotions
            )
            
            # Update session metrics
            self._update_session_metrics(session, conversation)
            
            return Response(
                ConversationSerializer(conversation).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        session = self.get_object()
        if session.is_completed:
            return Response(
                {'error': 'Session is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.end_time = timezone.now()
        session.duration = session.end_time - session.start_time
        session.is_completed = True
        session.save()
        
        # Update learning progress
        progress, _ = LearningProgress.objects.get_or_create(
            student=session.student,
            context=session.context,
            difficulty_level=session.context.difficulty_level
        )
        
        progress.sessions_completed += 1
        progress.total_duration += session.duration
        progress.last_session_date = session.end_time
        
        # Calculate average scores
        avg_scores = AISession.objects.filter(
            student=session.student,
            context=session.context,
            is_completed=True
        ).aggregate(
            avg_pronunciation=Avg('pronunciation_score'),
            avg_fluency=Avg('fluency_score'),
            avg_vocabulary=Avg('vocabulary_score'),
            avg_grammar=Avg('grammar_score')
        )
        
        progress.average_score = sum(
            score for score in avg_scores.values() if score is not None
        ) / len([score for score in avg_scores.values() if score is not None])
        
        progress.save()
        
        return Response(AISessionSerializer(session).data)
    
    def _generate_ai_response(self, context, user_input, emotions):
        # TODO: Implement AI response generation using context and emotions
        pass
    
    def _update_session_metrics(self, session, conversation):
        # TODO: Implement session metrics update
        pass

class LearningProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LearningProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LearningProgress.objects.filter(student__user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        progress = self.get_queryset()
        
        summary_data = {
            'total_sessions': sum(p.sessions_completed for p in progress),
            'total_duration': sum((p.total_duration for p in progress), timezone.timedelta()),
            'average_score': progress.aggregate(Avg('average_score'))['average_score__avg'],
            'contexts_started': progress.count(),
            'contexts_by_difficulty': {
                level: progress.filter(difficulty_level=level).count()
                for level, _ in LearningContext.DIFFICULTY_LEVELS
            }
        }
        
        return Response(summary_data)
