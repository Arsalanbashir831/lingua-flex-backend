from rest_framework import serializers
from .models import (
    User, File, Student, Teacher, TeacherCertificate, 
    TimeSlot, TeacherGig, Session, SessionBilling, AIConversation
)

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()
    
    def get_profile_picture(self, obj):
        """Return proper Supabase URL for profile picture"""
        if not obj.profile_picture:
            return None
        
        from django.conf import settings
        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"
        
        # Construct full Supabase URL
        return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{obj.profile_picture}"

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name", 
            "role", "phone_number", "gender", "date_of_birth", 
            "profile_picture", "created_at"
        ]
        read_only_fields = ["id", "email", "created_at", "full_name"]

class TeacherCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherCertificate
        fields = ['id', 'name', 'issuing_organization', 'issue_date', 'certificate_file', 'verified']
        read_only_fields = ['verified']

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'is_available']

class TeacherProfileSerializer(serializers.ModelSerializer):
    certificates = TeacherCertificateSerializer(many=True, read_only=True)
    availability = TimeSlotSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'user', 'qualifications', 'years_of_experience',
            'certificates', 'availability', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'learning_goals', 'proficiency_level', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class TeacherGigSerializer(serializers.ModelSerializer):
    teacher = TeacherProfileSerializer(read_only=True)

    class Meta:
        model = TeacherGig
        fields = [
            'id', 'teacher', 'category', 'title', 'description',
            'hourly_rate', 'language', 'experience_description',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class SessionSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)
    teacher = TeacherProfileSerializer(read_only=True)
    gig = TeacherGigSerializer(read_only=True)

    class Meta:
        model = Session
        fields = [
            'id', 'student', 'teacher', 'gig', 'scheduled_start',
            'scheduled_end', 'actual_start', 'actual_end', 'status',
            'zoom_meeting_id', 'zoom_join_url', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'actual_start', 'actual_end', 'zoom_meeting_id',
            'zoom_join_url', 'created_at', 'updated_at'
        ]

class SessionBillingSerializer(serializers.ModelSerializer):
    session = SessionSerializer(read_only=True)

    class Meta:
        model = SessionBilling
        fields = [
            'id', 'session', 'amount', 'duration_minutes',
            'is_paid', 'payment_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class AIConversationSerializer(serializers.ModelSerializer):
    student = StudentProfileSerializer(read_only=True)

    class Meta:
        model = AIConversation
        fields = [
            'id', 'student', 'language', 'context', 'voice_avatar',
            'duration_minutes', 'feedback', 'created_at'
        ]
        read_only_fields = ['created_at']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "filename", "file", "uploaded_at", "storage_key", "chroma_collection"]
        read_only_fields = ["id", "uploaded_at"]

class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    full_name = serializers.CharField(max_length=255)
    role = serializers.ChoiceField(choices=User.Role.choices)
    
    # Optional fields
    bio = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    native_language = serializers.CharField(required=False, allow_blank=True)
    learning_language = serializers.CharField(required=False, allow_blank=True)
    
    # Teacher specific fields
    qualifications = serializers.CharField(required=False, allow_blank=True)
    years_of_experience = serializers.IntegerField(required=False)

    def get_name_parts(self, full_name):
        parts = full_name.strip().split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ''

    def validate(self, data):
        if data.get('role') == User.Role.TEACHER:
            if not data.get('qualifications'):
                raise serializers.ValidationError(
                    {"qualifications": "Qualifications are required for teachers"}
                )
            if not data.get('years_of_experience'):
                raise serializers.ValidationError(
                    {"years_of_experience": "Years of experience is required for teachers"}
                )
        return data
