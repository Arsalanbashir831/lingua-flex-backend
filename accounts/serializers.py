from rest_framework import serializers
from .models import UserProfile, TeacherProfile, Language, Chat, Message, Gig, VoiceConversation
from core.serializers import UserSerializer
from core.models import User

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'code', 'is_active']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'bio', 'city', 'country', 'postal_code',
                 'status', 'native_language', 'learning_language', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class TeacherProfileSerializer(serializers.ModelSerializer):
    user_profile = UserProfileSerializer(read_only=True)
    certificates = serializers.JSONField()

    class Meta:
        model = TeacherProfile
        fields = ['id', 'user_profile', 'qualification', 'experience_years', 
                 'certificates', 'about']

class TeacherProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['qualification', 'experience_years', 'certificates', 'about']

class ComprehensiveTeacherProfileSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for updating all teacher information at once"""
    
    # User model fields
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    # UserProfile fields
    bio = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    native_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    learning_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # TeacherProfile fields
    qualification = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False)
    certificates = serializers.JSONField(required=False)
    about = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = TeacherProfile
        fields = [
            # User fields
            'first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth',
            # UserProfile fields  
            'bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language',
            # TeacherProfile fields
            'qualification', 'experience_years', 'certificates', 'about'
        ]
    
    def update(self, instance, validated_data):
        """Update User, UserProfile, and TeacherProfile in one transaction"""
        from django.db import transaction
        
        with transaction.atomic():
            # Extract User model fields
            user_fields = {}
            for field in ['first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth']:
                if field in validated_data:
                    user_fields[field] = validated_data.pop(field)
            
            # Extract UserProfile fields
            user_profile_fields = {}
            for field in ['bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language']:
                if field in validated_data:
                    user_profile_fields[field] = validated_data.pop(field)
            
            # Update User model
            if user_fields:
                user = instance.user_profile.user
                for field, value in user_fields.items():
                    setattr(user, field, value)
                user.save()
            
            # Update UserProfile model
            if user_profile_fields:
                user_profile = instance.user_profile
                for field, value in user_profile_fields.items():
                    setattr(user_profile, field, value)
                user_profile.save()
            
            # Update TeacherProfile model (remaining fields)
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()
            
        return instance
    
    def to_representation(self, instance):
        """Return comprehensive representation including all related data"""
        from django.conf import settings
        
        data = {}
        
        # User fields
        user = instance.user_profile.user
        
        # Construct profile picture URL if exists
        profile_picture_url = None
        if user.profile_picture:
            supabase_url = settings.SUPABASE_URL
            bucket_name = "user-uploads"
            profile_picture_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user.profile_picture}"
        
        data.update({
            'id': user.id,  # Add user ID
            'email': user.email,  # Add user email
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth,
            'role': user.role,  # Add user role
            'profile_picture': profile_picture_url,  # Add profile picture URL
            'created_at': user.created_at,  # Add created_at from user
        })
        
        # UserProfile fields
        user_profile = instance.user_profile
        data.update({
            'bio': user_profile.bio,
            'city': user_profile.city,
            'country': user_profile.country,
            'postal_code': user_profile.postal_code,
            'status': user_profile.status,
            'native_language': user_profile.native_language,
            'learning_language': user_profile.learning_language,
        })
        
        # TeacherProfile fields
        data.update({
            'qualification': instance.qualification,
            'experience_years': instance.experience_years,
            'certificates': instance.certificates,
            'about': instance.about,
        })
        
        return data

class ComprehensiveUserProfileSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for updating all student/user information at once"""
    
    # User model fields
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    # UserProfile fields
    bio = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    native_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    learning_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    class Meta:
        model = UserProfile
        fields = [
            # User fields
            'first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth',
            # UserProfile fields  
            'bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language'
        ]
    
    def update(self, instance, validated_data):
        """Update User and UserProfile in one transaction"""
        from django.db import transaction
        
        with transaction.atomic():
            # Extract User model fields
            user_fields = {}
            for field in ['first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth']:
                if field in validated_data:
                    user_fields[field] = validated_data.pop(field)
            
            # Update User model
            if user_fields:
                user = instance.user
                for field, value in user_fields.items():
                    setattr(user, field, value)
                user.save()
            
            # Update UserProfile model (remaining fields)
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()
            
        return instance
    
    def to_representation(self, instance):
        """Return comprehensive representation including all related data"""
        from django.conf import settings
        
        data = {}
        
        # User fields
        user = instance.user
        
        # Construct profile picture URL if exists
        profile_picture_url = None
        if user.profile_picture:
            supabase_url = settings.SUPABASE_URL
            bucket_name = "user-uploads"
            profile_picture_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user.profile_picture}"
        
        data.update({
            'id': user.id,  # Add user ID
            'email': user.email,  # Add user email
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth,
            'role': user.role,  # Add user role
            'profile_picture': profile_picture_url,  # Add profile picture URL
            'created_at': user.created_at,  # Add created_at from user
        })
        
        # UserProfile fields
        data.update({
            'bio': instance.bio,
            'city': instance.city,
            'country': instance.country,
            'postal_code': instance.postal_code,
            'status': instance.status,
            'native_language': instance.native_language,
            'learning_language': instance.learning_language,
        })
        
        return data

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
class GigTeacherSerializer(serializers.ModelSerializer):
    """Serializer for teacher details in gig responses"""
    # User details
    id = serializers.CharField(source='user_profile.user.id', read_only=True)
    email = serializers.EmailField(source='user_profile.user.email', read_only=True)
    first_name = serializers.CharField(source='user_profile.user.first_name', read_only=True)
    last_name = serializers.CharField(source='user_profile.user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    
    # Teacher profile details
    qualification = serializers.CharField(read_only=True)
    experience_years = serializers.IntegerField(read_only=True)
    about = serializers.CharField(read_only=True)
    
    # User profile details
    bio = serializers.CharField(source='user_profile.bio', read_only=True)
    city = serializers.CharField(source='user_profile.city', read_only=True)
    country = serializers.CharField(source='user_profile.country', read_only=True)
    native_language = serializers.CharField(source='user_profile.native_language', read_only=True)
    
    def get_full_name(self, obj):
        user = obj.user_profile.user
        return f"{user.first_name or ''} {user.last_name or ''}".strip()
    
    def get_profile_picture(self, obj):
        user = obj.user_profile.user
        if not user.profile_picture:
            return None
        
        from django.conf import settings
        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"
        return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user.profile_picture}"

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'profile_picture',
            'qualification', 'experience_years', 'about', 'bio', 'city', 'country', 'native_language'
        ]

class GigSerializer(serializers.ModelSerializer):
    teacher_details = GigTeacherSerializer(source='teacher', read_only=True)
    
    class Meta:
        model = Gig
        fields = [
            'id', 'teacher', 'teacher_details', 'category', 'service_type', 'service_title', 'short_description',
            'full_description', 'price_per_session', 'session_duration', 'tags', 'what_you_provide_in_session',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher', 'created_at', 'updated_at']

class VoiceConversationSerializer(serializers.ModelSerializer):
    """Serializer for OpenAI speech-to-speech voice conversations"""
    
    # Read-only fields for response
    user_name = serializers.SerializerMethodField()
    user_email = serializers.CharField(source='user.email', read_only=True)
    conversation_type_display = serializers.CharField(source='get_conversation_type_display', read_only=True)
    
    class Meta:
        model = VoiceConversation
        fields = [
            'id', 'user', 'user_name', 'user_email', 'topic', 'transcription',
            'native_language', 'target_language', 'conversation_type', 'conversation_type_display',
            'duration_minutes', 'ai_feedback', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def get_user_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip() or obj.user.email
    
    def validate_transcription(self, value):
        """Validate transcription is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Transcription cannot be empty.")
        return value.strip()
    
    def validate_topic(self, value):
        """Validate topic is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        return value.strip()

class VoiceConversationCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating voice conversations from frontend"""
    
    class Meta:
        model = VoiceConversation
        fields = [
            'topic', 'transcription', 'native_language', 'target_language',
            'conversation_type', 'duration_minutes', 'ai_feedback'
        ]
    
    def validate_transcription(self, value):
        """Validate transcription JSON object"""
        if value is None:
            raise serializers.ValidationError("Transcription cannot be null.")
        
        if isinstance(value, dict):
            # Accept any dictionary structure - no specific requirements
            return value
        
        elif isinstance(value, str):
            # If receiving string, convert to JSON format
            if not value.strip():
                raise serializers.ValidationError("Transcription cannot be empty.")
            
            return {
                "full_text": value.strip(),
                "format": "text",
                "metadata": {
                    "converted_from_string": True
                }
            }
        
        else:
            raise serializers.ValidationError(
                "Transcription must be a JSON object or string."
            )
    
    def validate_topic(self, value):
        """Validate topic is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Topic cannot be empty.")
        return value.strip()
    
    def create(self, validated_data):
        """Create conversation with authenticated user"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
