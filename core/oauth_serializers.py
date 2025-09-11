"""
Serializers for Google OAuth authentication
"""
from rest_framework import serializers
from core.models import User


class GoogleOAuthInitiateSerializer(serializers.Serializer):
    """Serializer for initiating Google OAuth flow"""
    role = serializers.ChoiceField(choices=User.Role.choices, required=False, help_text="Role for new user registration (optional for existing users)")
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
    """Serializer for completing OAuth user profile - matches RegisterWithProfileView fields exactly"""
    
    # Core User model fields
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    # UserProfile (accounts model) fields - created for ALL users
    bio = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    status = serializers.CharField(max_length=100, required=False, allow_blank=True)
    native_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    learning_language = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    # TeacherProfile (accounts model) fields - for teachers only
    qualification = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, min_value=0)
    certificates = serializers.JSONField(required=False, default=list)
    about = serializers.CharField(required=False, allow_blank=True)  # TeacherProfile.about field
    
    # Teacher (core model) fields - for teachers only (for booking system)
    teaching_experience = serializers.IntegerField(required=False, min_value=0)
    teaching_languages = serializers.JSONField(required=False, default=list)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, min_value=0)
    
    # NOTE: No Student model fields - RegisterWithProfileView doesn't create Student model
    # Student-specific fields can be added to UserProfile or handled separately if needed
    
    def validate(self, data):
        """Validate based on user role"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.role == User.Role.TEACHER:
                # For teachers, some fields might be required based on business logic
                pass  # Add validation rules if needed
            elif user.role == User.Role.STUDENT:
                # For students, only UserProfile fields are relevant
                pass  # Add validation rules if needed
        
        return data
