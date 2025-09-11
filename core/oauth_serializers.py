"""
Serializers for Google OAuth authentication
"""
from rest_framework import serializers
from core.models import User


class GoogleOAuthInitiateSerializer(serializers.Serializer):
    """Serializer for initiating Google OAuth flow"""
    role = serializers.ChoiceField(choices=User.Role.choices)
    redirect_url = serializers.URLField(required=False, help_text="Frontend URL to redirect after OAuth")


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
            'id', 'email', 'first_name', 'last_name', 'full_name', 
            'role', 'auth_provider', 'email_verified', 'is_oauth_user',
            'created_at'
        ]
        read_only_fields = ['id', 'auth_provider', 'email_verified', 'is_oauth_user', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class GoogleOAuthCompleteProfileSerializer(serializers.Serializer):
    """Serializer for completing OAuth user profile"""
    # Common fields
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    # Teacher-specific fields
    bio = serializers.CharField(required=False, allow_blank=True)
    teaching_experience = serializers.IntegerField(required=False, min_value=0)
    teaching_languages = serializers.JSONField(required=False, default=list)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    
    # Student-specific fields
    learning_goals = serializers.CharField(required=False, allow_blank=True)
    proficiency_level = serializers.ChoiceField(
        choices=[('BEGINNER', 'Beginner'), ('INTERMEDIATE', 'Intermediate'), ('ADVANCED', 'Advanced')],
        required=False
    )
    target_languages = serializers.JSONField(required=False, default=list)
    
    def validate(self, data):
        """Validate based on user role"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.role == User.Role.TEACHER:
                # For teachers, require bio
                if not data.get('bio'):
                    raise serializers.ValidationError({'bio': 'Bio is required for teachers'})
            elif user.role == User.Role.STUDENT:
                # For students, require proficiency level
                if not data.get('proficiency_level'):
                    raise serializers.ValidationError({'proficiency_level': 'Proficiency level is required for students'})
        
        return data
