from rest_framework import serializers
from .models import VoiceAvatar, LearningContext, AISession, Conversation, LearningProgress
from accounts.serializers import UserProfileSerializer, LanguageSerializer

class VoiceAvatarSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)
    
    class Meta:
        model = VoiceAvatar
        fields = ['id', 'name', 'language', 'accent', 'voice_id', 'description',
                 'gender', 'age_range', 'is_active', 'sample_audio_url']

class LearningContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningContext
        fields = ['id', 'name', 'description', 'category', 'difficulty_level',
                 'vocabulary', 'suggested_responses', 'is_active']

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'session', 'timestamp', 'user_input', 'ai_response',
                 'user_audio_url', 'ai_audio_url', 'emotion_metrics',
                 'pronunciation_feedback']
        read_only_fields = ['timestamp', 'ai_response', 'ai_audio_url',
                           'emotion_metrics', 'pronunciation_feedback']

class AISessionSerializer(serializers.ModelSerializer):
    student = UserProfileSerializer(read_only=True)
    voice_avatar = VoiceAvatarSerializer(read_only=True)
    context = LearningContextSerializer(read_only=True)
    conversations = ConversationSerializer(many=True, read_only=True)
    
    class Meta:
        model = AISession
        fields = ['id', 'student', 'voice_avatar', 'context', 'start_time',
                 'end_time', 'duration', 'feedback', 'performance_metrics',
                 'pronunciation_score', 'fluency_score', 'vocabulary_score',
                 'grammar_score', 'notes', 'is_completed', 'conversations']
        read_only_fields = ['start_time', 'end_time', 'duration',
                           'performance_metrics', 'pronunciation_score',
                           'fluency_score', 'vocabulary_score', 'grammar_score']

class AISessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISession
        fields = ['voice_avatar', 'context']

class LearningProgressSerializer(serializers.ModelSerializer):
    student = UserProfileSerializer(read_only=True)
    context = LearningContextSerializer(read_only=True)
    
    class Meta:
        model = LearningProgress
        fields = ['id', 'student', 'context', 'difficulty_level',
                 'sessions_completed', 'total_duration', 'average_score',
                 'mastered_vocabulary', 'areas_for_improvement',
                 'last_session_date']
        read_only_fields = ['sessions_completed', 'total_duration',
                           'average_score', 'last_session_date']
