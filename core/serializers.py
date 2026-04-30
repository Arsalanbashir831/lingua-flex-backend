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
        parts = full_name.strip().split(" ", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ""

    def validate(self, data):
        if data.get("role") == User.Role.TEACHER:
            if not data.get("qualifications"):
                raise serializers.ValidationError(
                    {"qualifications": "Qualifications are required for teachers"}
                )
            if not data.get("years_of_experience"):
                raise serializers.ValidationError(
                    {
                        "years_of_experience": "Years of experience is required for teachers"
                    }
                )
        return data


# --- Google OAuth Serializers ---


class GoogleOAuthInitiateSerializer(serializers.Serializer):
    """Serializer for initiating Google OAuth flow"""

    role = serializers.ChoiceField(
        choices=User.Role.choices,
        required=False,
        help_text="Role for new user registration (optional for existing users)",
    )
    redirect_url = serializers.URLField(
        required=False, help_text="Frontend URL to redirect after OAuth"
    )


class GoogleOAuthCallbackSerializer(serializers.Serializer):
    """Serializer for handling Google OAuth callback"""

    access_token = serializers.CharField(help_text="Access token from Supabase OAuth")
    refresh_token = serializers.CharField(required=False)
    role = serializers.ChoiceField(choices=User.Role.choices, required=False)


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
