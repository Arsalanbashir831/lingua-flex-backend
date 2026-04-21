from rest_framework import serializers
from .models import BirthProfile, AstrologyDashboardAccess, AstrologyChat
from core.models import User


class BirthProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BirthProfile
        fields = [
            'id', 'user_name',
            'birth_year', 'birth_month', 'birth_day',
            'birth_hour', 'birth_minute',
            'city', 'country_code',
            'timezone_str', 'created_at', 'updated_at',
            'guest_name', 'created_by'
        ]
        read_only_fields = ['id', 'user_name', 'timezone_str', 'created_at', 'updated_at', 'created_by']

    def get_user_name(self, obj):
        return obj.display_name


class UserBasicSerializer(serializers.ModelSerializer):
    """Minimal user info for access-related responses."""
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_picture']

    def get_full_name(self, obj):
        return obj.get_full_name() or "User"

    def get_profile_picture(self, obj):
        if not obj.profile_picture:
            return None
        from django.conf import settings
        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"
        return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{obj.profile_picture}"


class AstrologyAccessSerializer(serializers.ModelSerializer):
    """
    Used by students to see which teachers have access to their dashboard.
    """
    teacher = UserBasicSerializer(read_only=True)

    class Meta:
        model = AstrologyDashboardAccess
        fields = ['id', 'teacher', 'granted_at']


class StudentDashboardSummarySerializer(serializers.ModelSerializer):
    """
    Used by teachers to list students whose dashboards they can view.
    """
    student = UserBasicSerializer(read_only=True)
    has_birth_profile = serializers.SerializerMethodField()

    class Meta:
        model = AstrologyDashboardAccess
        fields = ['id', 'student', 'has_birth_profile', 'granted_at']

    def get_has_birth_profile(self, obj):
        return hasattr(obj.student, 'birth_profile')


class AstrologyChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstrologyChat
        fields = ['id', 'category', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'category', 'role', 'content', 'created_at']
