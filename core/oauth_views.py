"""
Google OAuth authentication views for LinguaFlex
"""
import logging
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from django.db import transaction
from django.db import models
from supabase import create_client
from gotrue.errors import AuthApiError

from core.models import User, Teacher
from accounts.models import UserProfile, TeacherProfile
from core.oauth_serializers import (
    GoogleOAuthInitiateSerializer,
    GoogleOAuthCallbackSerializer,
    GoogleOAuthUserSerializer,
    GoogleOAuthCompleteProfileSerializer
)

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class GoogleOAuthInitiateView(APIView):
    """
    Initiate Google OAuth flow with optional role selection
    
    POST /api/auth/google/initiate/
    {
        "role": "STUDENT" | "TEACHER",  # optional - required for new users, optional for existing users
        "redirect_url": "https://yourfrontend.com/auth/callback"  # optional
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = GoogleOAuthInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        role = data.get('role')  # Optional now
        redirect_url = data.get('redirect_url', settings.BASE_URL_SIGNIN)
        
        try:
            # Generate OAuth URL through Supabase
            # The frontend will redirect user to this URL
            oauth_url = f"{settings.SUPABASE_URL}/auth/v1/authorize"
            params = {
                'provider': 'google',
                'redirect_to': redirect_url,
                'scopes': 'openid email profile'
            }
            
            # Build full OAuth URL
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_oauth_url = f"{oauth_url}?{param_string}"
            
            response_data = {
                'success': True,
                'oauth_url': full_oauth_url,
                'message': 'Redirect user to oauth_url to complete Google authentication'
            }
            
            # # Include role in response if provided
            # if role:
            #     response_data['role'] = role
            #     response_data['flow_type'] = 'registration'
            # else:
            #     response_data['flow_type'] = 'login'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error initiating Google OAuth: {e}")
            return Response(
                {'success': False, 'error': f'Failed to initiate OAuth: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthCallbackView(APIView):
    """
    Handle Google OAuth callback and create/login user
    
    POST /api/auth/google/callback/
    {
        "access_token": "supabase_access_token",
        "refresh_token": "supabase_refresh_token",
        "role": "STUDENT" | "TEACHER"  # optional - only needed for new user registration
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = GoogleOAuthCallbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Invalid callback data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        access_token = data['access_token']
        refresh_token = data.get('refresh_token')
        provided_role = data.get('role')  # May be None for existing users
        
        try:
            # Get user data from Supabase using the access token
            supabase_user = supabase.auth.get_user(access_token)
            
            if not supabase_user.user:
                return Response(
                    {'success': False, 'error': 'Invalid access token'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            user_data = supabase_user.user
            email = user_data.email
            supabase_id = user_data.id
            
            # Extract name from user metadata or app_metadata
            user_metadata = user_data.user_metadata or {}
            first_name = user_metadata.get('first_name') or user_metadata.get('given_name', '')
            last_name = user_metadata.get('last_name') or user_metadata.get('family_name', '')
            full_name = user_metadata.get('full_name') or user_metadata.get('name', '')
            
            # If we don't have separate first/last names, try to split full name
            if not first_name and not last_name and full_name:
                name_parts = full_name.strip().split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Get Google ID from provider data
            google_id = None
            for identity in user_data.identities or []:
                if identity.provider == 'google':
                    google_id = identity.id
                    break
            
            with transaction.atomic():
                # Check if user already exists
                user = None
                created = False
                is_existing_user_login = False
                
                try:
                    # Try to find existing user by email or Supabase ID
                    user = User.objects.get(models.Q(email=email) | models.Q(id=supabase_id))
                    is_existing_user_login = True
                    
                    # Update OAuth information if this is first OAuth login
                    if not user.is_oauth_user:
                        user.is_oauth_user = True
                        user.auth_provider = User.AuthProvider.GOOGLE
                        user.google_id = google_id
                        user.email_verified = True
                        user.save()
                    
                except User.DoesNotExist:
                    # Create new OAuth user - REQUIRES role for new users
                    if not provided_role:
                        return Response(
                            {
                                'success': False, 
                                'error': 'Role is required for new user registration',
                                'requires_role_selection': True
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    user = User.objects.create_oauth_user(
                        id=supabase_id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=provided_role,
                        auth_provider=User.AuthProvider.GOOGLE,
                        google_id=google_id
                    )
                    created = True
                
                # Create role-specific profiles if user was just created - MATCH REGISTRATION EXACTLY
                if created:
                    # Use the provided role for new users
                    user_role = provided_role
                    
                    # Create UserProfile first (accounts model) - this is created for ALL users
                    user_profile = UserProfile.objects.create(
                        user=user,
                        role=user_role,
                        bio='',
                        city='',
                        country='',
                        postal_code='',
                        status='',
                        native_language='',
                        learning_language=''
                    )
                    
                    # Only create additional models for TEACHERS (same as RegisterWithProfileView)
                    if user_role == User.Role.TEACHER:
                        # Create TeacherProfile model (accounts model)
                        TeacherProfile.objects.create(
                            user_profile=user_profile,
                            qualification='',
                            experience_years=0,
                            certificates=[],
                            about=''
                        )
                        
                        # Create Teacher model (core model) - for booking system
                        Teacher.objects.create(
                            user=user,
                            bio='',  # Will be filled in profile completion
                            teaching_experience=0,
                            teaching_languages=[],
                            hourly_rate=0  # Default value, can be updated later
                        )
                    
                    # For STUDENTS: Only UserProfile is created (no Student model)
            
            # Serialize user data for response
            user_serializer = GoogleOAuthUserSerializer(user)
            
            return Response({
                'success': True,
                'message': f'User {"registered" if created else "logged in"} successfully via Google',
                'user': user_serializer.data,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'created': created,
                'is_existing_user_login': is_existing_user_login,
                'requires_profile_completion': created,  # New users need to complete profile
                'flow_type': 'registration' if created else 'login'
            }, status=status.HTTP_200_OK)
            
        except AuthApiError as e:
            logger.error(f"Supabase auth error: {e}")
            return Response(
                {'success': False, 'error': f'Authentication error: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Error in Google OAuth callback: {e}")
            return Response(
                {'success': False, 'error': f'OAuth callback failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthCompleteProfileView(APIView):
    """
    Complete profile setup for OAuth users - matches RegisterWithProfileView schema
    
    POST /api/auth/google/complete-profile/
    {
        // Common fields
        "phone_number": "+1234567890",
        "gender": "Male",
        "date_of_birth": "1990-01-01",
        
        // UserProfile (accounts model) fields
        "bio": "I love languages",
        "city": "New York",
        "country": "USA",
        "postal_code": "10001",
        "native_language": "English",
        "learning_language": "Spanish",
        
        // Teacher-specific fields (if role is TEACHER)
        "qualification": "TESOL Certified",
        "experience_years": 5,
        "certificates": ["cert1.pdf", "cert2.pdf"],
        "about": "Experienced teacher with 5 years...",
        "teaching_experience": 5,
        "teaching_languages": ["English", "Spanish"],
        "hourly_rate": 30.00,
        
        // Student-specific fields (if role is STUDENT)
        "learning_goals": "Improve conversational skills",
        "proficiency_level": "INTERMEDIATE",
        "target_languages": ["Spanish", "French"]
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Ensure user is OAuth user
        if not user.is_oauth_user:
            return Response(
                {'success': False, 'error': 'This endpoint is only for OAuth users'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = GoogleOAuthCompleteProfileSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Invalid profile data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            with transaction.atomic():
                # Update User model fields
                user_fields = ['phone_number', 'gender', 'date_of_birth']
                for field in user_fields:
                    if field in data and data[field] is not None:
                        setattr(user, field, data[field])
                user.save()
                
                # Update UserProfile (accounts model)
                try:
                    user_profile = user.profile
                except:
                    # Create profile if it doesn't exist (shouldn't happen with proper OAuth flow)
                    user_profile = UserProfile.objects.create(
                        user=user,
                        role=user.role
                    )
                
                # Update UserProfile fields
                profile_fields = ['bio', 'city', 'country', 'postal_code', 'status', 'native_language', 'learning_language']
                for field in profile_fields:
                    if field in data and data[field] is not None:
                        setattr(user_profile, field, data[field])
                user_profile.save()
                
                # Update role-specific profiles - MATCH REGISTRATION PATTERN
                if user.role == User.Role.TEACHER:
                    # Update Teacher model (core) - for booking system
                    try:
                        teacher = user.teacher
                    except Teacher.DoesNotExist:
                        teacher = Teacher.objects.create(
                            user=user,
                            bio='',
                            teaching_experience=0,
                            teaching_languages=[],
                            hourly_rate=0
                        )
                    
                    # Update Teacher fields
                    teacher_core_fields = {
                        'bio': data.get('bio', teacher.bio),
                        'teaching_experience': data.get('teaching_experience', teacher.teaching_experience),
                        'teaching_languages': data.get('teaching_languages', teacher.teaching_languages),
                        'hourly_rate': data.get('hourly_rate', teacher.hourly_rate)
                    }
                    for field, value in teacher_core_fields.items():
                        if value is not None:
                            setattr(teacher, field, value)
                    teacher.save()
                    
                    # Update TeacherProfile model (accounts)
                    try:
                        teacher_profile = user_profile.teacherprofile
                    except TeacherProfile.DoesNotExist:
                        teacher_profile = TeacherProfile.objects.create(
                            user_profile=user_profile,
                            qualification='',
                            experience_years=0,
                            certificates=[],
                            about=''
                        )
                    
                    # Update TeacherProfile fields
                    teacher_profile_fields = {
                        'qualification': data.get('qualification', teacher_profile.qualification),
                        'experience_years': data.get('experience_years', teacher_profile.experience_years),
                        'certificates': data.get('certificates', teacher_profile.certificates),
                        'about': data.get('about', teacher_profile.about)
                    }
                    for field, value in teacher_profile_fields.items():
                        if value is not None:
                            setattr(teacher_profile, field, value)
                    teacher_profile.save()
                    
                elif user.role == User.Role.STUDENT:
                    # For students, only update UserProfile (no Student model created in registration)
                    # Student-specific fields can be stored in UserProfile or handled separately if needed
                    # This matches the RegisterWithProfileView pattern
                    pass
            
            # Return updated user data
            user_serializer = GoogleOAuthUserSerializer(user)
            
            return Response({
                'success': True,
                'message': 'Profile completed successfully',
                'user': user_serializer.data,
                'profile_complete': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error completing OAuth profile: {e}")
            return Response(
                {'success': False, 'error': f'Failed to complete profile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleOAuthStatusView(APIView):
    """
    Get current user's OAuth status and profile completion status
    
    GET /api/auth/google/status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Check profile completion status based on the same schema as RegisterWithProfileView
        profile_complete = False
        profile_data = {}
        requires_profile_completion = False
        
        try:
            # Check if UserProfile exists and has basic info
            user_profile = user.profile
            has_basic_profile = bool(user_profile)
            
            if user.role == User.Role.TEACHER:
                # For teachers, check both Teacher and TeacherProfile models
                try:
                    teacher = user.teacher
                    teacher_profile = user_profile.teacherprofile
                    
                    # Consider profile complete if basic required fields are filled
                    profile_complete = bool(
                        teacher.bio and  # Teacher model bio
                        teacher.teaching_experience >= 0 and  # Teaching experience
                        teacher_profile.qualification and  # TeacherProfile qualification
                        teacher_profile.experience_years >= 0  # TeacherProfile experience
                    )
                    
                    profile_data = {
                        'user_profile': {
                            'bio': user_profile.bio,
                            'city': user_profile.city,
                            'country': user_profile.country,
                            'native_language': user_profile.native_language,
                            'learning_language': user_profile.learning_language,
                        },
                        'teacher_core': {
                            'bio': teacher.bio,
                            'teaching_experience': teacher.teaching_experience,
                            'teaching_languages': teacher.teaching_languages,
                            'hourly_rate': str(teacher.hourly_rate),
                        },
                        'teacher_profile': {
                            'qualification': teacher_profile.qualification,
                            'experience_years': teacher_profile.experience_years,
                            'certificates': teacher_profile.certificates,
                            'about': teacher_profile.about,
                        }
                    }
                    
                except (Teacher.DoesNotExist, TeacherProfile.DoesNotExist):
                    profile_complete = False
                    requires_profile_completion = True
                    
            elif user.role == User.Role.STUDENT:
                # For students, only check UserProfile (no Student model in RegisterWithProfileView)
                try:
                    # Consider profile complete if UserProfile has basic info
                    profile_complete = bool(
                        user_profile and  # UserProfile exists
                        user_profile.role == User.Role.STUDENT  # Role is set correctly
                    )
                    
                    profile_data = {
                        'user_profile': {
                            'bio': user_profile.bio,
                            'city': user_profile.city,
                            'country': user_profile.country,
                            'native_language': user_profile.native_language,
                            'learning_language': user_profile.learning_language,
                        }
                        # No student model to check - matches RegisterWithProfileView pattern
                    }
                    
                except Exception:
                    profile_complete = False
                    requires_profile_completion = True
                    
            # If OAuth user doesn't have profile, they need to complete it
            if user.is_oauth_user and not profile_complete:
                requires_profile_completion = True
                
        except Exception as e:
            # If UserProfile doesn't exist, definitely need profile completion
            requires_profile_completion = user.is_oauth_user
            logger.error(f"Error checking profile status: {e}")
        
        # Serialize user data
        user_serializer = GoogleOAuthUserSerializer(user)
        
        return Response({
            'success': True,
            'user': user_serializer.data,
            'is_oauth_user': user.is_oauth_user,
            'auth_provider': user.auth_provider,
            'profile_complete': profile_complete,
            'requires_profile_completion': requires_profile_completion,
            'profile_data': profile_data,
            'next_steps': self._get_next_steps(user, profile_complete, requires_profile_completion)
        }, status=status.HTTP_200_OK)
    
    def _get_next_steps(self, user, profile_complete, requires_profile_completion):
        """Get recommended next steps for the user"""
        steps = []
        
        if requires_profile_completion:
            if user.role == User.Role.TEACHER:
                steps.append("Complete your teaching profile with bio, qualifications, and experience")
                steps.append("Set your hourly rate and teaching languages")
                steps.append("Upload teaching certificates (optional)")
            elif user.role == User.Role.STUDENT:
                steps.append("Complete your profile with learning preferences")
                steps.append("Add your location and contact information")
                steps.append("Set your native and target languages")
        
        elif profile_complete:
            if user.role == User.Role.TEACHER:
                steps.append("Your profile is complete! Start accepting bookings")
                steps.append("Update your availability and teaching schedule")
            elif user.role == User.Role.STUDENT:
                steps.append("Your profile is complete! Start booking lessons")
                steps.append("Browse available teachers and subjects")
        
        return steps
