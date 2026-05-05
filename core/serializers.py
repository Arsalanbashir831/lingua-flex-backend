from rest_framework import serializers
from .models import User


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
        bucket_name = getattr(settings, "SUPABASE_USER_UPLOADS_BUCKET", "user-uploads")

        # Construct full Supabase URL
        return f"{supabase_url}/storage/v1/object/public/{bucket_name}/{obj.profile_picture}"

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "phone_number",
            "gender",
            "date_of_birth",
            "profile_picture",
            "created_at",
        ]
        read_only_fields = ["id", "email", "created_at", "full_name"]


# --- Google OAuth Serializers ---


class SyncSupabaseUserSerializer(serializers.Serializer):
    """Serializer for syncing Supabase user to local database"""

    access_token = serializers.CharField(help_text="Access token from Supabase OAuth (JWT)")
    role = serializers.ChoiceField(choices=User.Role.choices, required=False, help_text="Role for new user registration (optional)")


class SetUserRoleSerializer(serializers.Serializer):
    """Serializer for setting user role post-signup"""

    role = serializers.ChoiceField(choices=User.Role.choices, help_text="Role to assign to the user")


class GoogleOAuthUserSerializer(serializers.ModelSerializer):
    """Serializer for OAuth user data"""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "auth_provider",
            "email_verified",
            "is_oauth_user",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "auth_provider",
            "email_verified",
            "is_oauth_user",
            "created_at",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()
