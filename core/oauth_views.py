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

from core.models import User, Student, Teacher
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
    Initiate Google OAuth flow with role selection
    
    POST /api/auth/google/initiate/
    {
        "role": "STUDENT" | "TEACHER",
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
        role = data['role']
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
            
            # Add role to state parameter so we can retrieve it after OAuth
            state_data = {'role': role}
            
            # Build full OAuth URL
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            full_oauth_url = f"{oauth_url}?{param_string}"
            
            return Response({
                'success': True,
                'oauth_url': full_oauth_url,
                'role': role,
                'message': 'Redirect user to oauth_url to complete Google authentication'
            }, status=status.HTTP_200_OK)
            
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
        "role": "STUDENT" | "TEACHER"
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
        role = data.get('role', User.Role.STUDENT)
        
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
                
                try:
                    # Try to find existing user by email or Supabase ID
                    user = User.objects.get(models.Q(email=email) | models.Q(id=supabase_id))
                    
                    # Update OAuth information if this is first OAuth login
                    if not user.is_oauth_user:
                        user.is_oauth_user = True
                        user.auth_provider = User.AuthProvider.GOOGLE
                        user.google_id = google_id
                        user.email_verified = True
                        user.save()
                    
                except User.DoesNotExist:
                    # Create new OAuth user
                    user = User.objects.create_oauth_user(
                        id=supabase_id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        auth_provider=User.AuthProvider.GOOGLE,
                        google_id=google_id
                    )
                    created = True
                
                # Create role-specific profile if user was just created
                if created:
                    if role == User.Role.STUDENT:
                        Student.objects.create(
                            user=user,
                            proficiency_level='BEGINNER',  # Default
                            target_languages=[]
                        )
                    elif role == User.Role.TEACHER:
                        Teacher.objects.create(
                            user=user,
                            bio='',  # Will be filled in profile completion
                            teaching_experience=0,
                            teaching_languages=[],
                            hourly_rate=25.00  # Default
                        )
            
            # Serialize user data for response
            user_serializer = GoogleOAuthUserSerializer(user)
            
            return Response({
                'success': True,
                'message': 'User authenticated successfully via Google',
                'user': user_serializer.data,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'created': created,
                'requires_profile_completion': created  # New users need to complete profile
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
    Complete profile setup for OAuth users
    
    POST /api/auth/google/complete-profile/
    {
        "bio": "I'm a passionate language teacher...",  # for teachers
        "teaching_experience": 5,  # for teachers
        "proficiency_level": "INTERMEDIATE"  # for students
        // ... other profile fields
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
                # Update user common fields
                for field in ['phone_number', 'gender', 'date_of_birth']:
                    if field in data and data[field] is not None:
                        setattr(user, field, data[field])
                user.save()
                
                # Update role-specific profile
                if user.role == User.Role.TEACHER:
                    teacher_profile = Teacher.objects.get(user=user)
                    teacher_profile.bio = data.get('bio', teacher_profile.bio)
                    teacher_profile.teaching_experience = data.get('teaching_experience', teacher_profile.teaching_experience)
                    teacher_profile.teaching_languages = data.get('teaching_languages', teacher_profile.teaching_languages)
                    teacher_profile.hourly_rate = data.get('hourly_rate', teacher_profile.hourly_rate)
                    teacher_profile.save()
                    
                elif user.role == User.Role.STUDENT:
                    student_profile = Student.objects.get(user=user)
                    student_profile.learning_goals = data.get('learning_goals', student_profile.learning_goals)
                    student_profile.proficiency_level = data.get('proficiency_level', student_profile.proficiency_level)
                    student_profile.target_languages = data.get('target_languages', student_profile.target_languages)
                    student_profile.save()
            
            # Return updated user data
            user_serializer = GoogleOAuthUserSerializer(user)
            
            return Response({
                'success': True,
                'message': 'Profile completed successfully',
                'user': user_serializer.data
            }, status=status.HTTP_200_OK)
            
        except (Student.DoesNotExist, Teacher.DoesNotExist) as e:
            return Response(
                {'success': False, 'error': f'User profile not found: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
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
        
        # Check profile completion status
        profile_complete = False
        profile_data = {}
        
        try:
            if user.role == User.Role.TEACHER and hasattr(user, 'teacher'):
                teacher = user.teacher
                profile_complete = bool(teacher.bio and teacher.teaching_experience >= 0)
                profile_data = {
                    'bio': teacher.bio,
                    'teaching_experience': teacher.teaching_experience,
                    'teaching_languages': teacher.teaching_languages,
                    'hourly_rate': str(teacher.hourly_rate)
                }
            elif user.role == User.Role.STUDENT and hasattr(user, 'student'):
                student = user.student
                profile_complete = bool(student.proficiency_level)
                profile_data = {
                    'learning_goals': student.learning_goals,
                    'proficiency_level': student.proficiency_level,
                    'target_languages': student.target_languages
                }
        except (AttributeError, Student.DoesNotExist, Teacher.DoesNotExist):
            profile_complete = False
        
        user_serializer = GoogleOAuthUserSerializer(user)
        
        return Response({
            'success': True,
            'user': user_serializer.data,
            'is_oauth_user': user.is_oauth_user,
            'auth_provider': user.auth_provider,
            'profile_complete': profile_complete,
            'profile_data': profile_data
        }, status=status.HTTP_200_OK)
