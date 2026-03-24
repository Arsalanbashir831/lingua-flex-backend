# accounts/serializers.py
from rest_framework import serializers
from .models import UserProfile, TeacherProfile, Language, Chat, Message, Gig
from core.serializers import UserSerializer
from core.models import User

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code', 'is_active']

# Simplified registration serializer - only basic required fields
class SimpleUserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=['student', 'teacher'])

    def validate_role(self, value):
        if value.lower() not in ['student', 'teacher']:
            raise serializers.ValidationError("Role must be either 'student' or 'teacher'")
        return value.lower()

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'bio', 'city', 'country', 'postal_code',
                 'status', 'native_language', 'learning_language', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'role', 'created_at', 'updated_at']

# Separate serializer for updating student profile
class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language']

class TeacherProfileSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    certificates = serializers.JSONField()

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user_profile', 'qualification', 'experience_years', 
                 'certificates', 'about']

# Separate serializer for creating/updating teacher-specific profile
class TeacherProfileUpdateSerializer(serializers.ModelSerializer):
    # Include user profile fields for convenience
    bio = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    native_language = serializers.CharField(required=False, allow_blank=True)
    learning_language = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = TeacherProfile
        fields = ['qualification', 'experience_years', 'certificates', 'about',
                 'bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language']

    def update(self, instance, validated_data):
        # Extract user profile fields
        user_profile_fields = {
            'bio': validated_data.pop('bio', None),
            'city': validated_data.pop('city', None),
            'country': validated_data.pop('country', None),
            'postal_code': validated_data.pop('postal_code', None),
            'status': validated_data.pop('status', None),
            'native_language': validated_data.pop('native_language', None),
            'learning_language': validated_data.pop('learning_language', None),
        }

        # Update teacher profile fields
        for attr, value in validated_data.items():
            if value is not None:
                setattr(instance, attr, value)
        instance.save()

        # Update user profile fields
        user_profile = instance.user_profile
        for attr, value in user_profile_fields.items():
            if value is not None:
                setattr(user_profile, attr, value)
        user_profile.save()

        return instance

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'content', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'sender']

class ChatSerializer(serializers.ModelSerializer):
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'participant1', 'participant2', 'created_at', 'messages']

class GigSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.user_profile.user.get_full_name', read_only=True)
    
    class Meta:
        model = Gig
        fields = [
            'id', 'teacher', 'teacher_name', 'category', 'service_type', 'service_title', 
            'short_description', 'full_description', 'price_per_session', 'session_duration', 
            'tags', 'what_you_provide_in_session', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher', 'teacher_name', 'created_at', 'updated_at']
