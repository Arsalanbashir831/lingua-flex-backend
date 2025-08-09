# accounts/views_new.py
from rest_framework import generics, status, viewsets
from rest_framework import serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from django.db import transaction, models
from .models import UserProfile, TeacherProfile, Language, Chat, Message, Gig
from .serializers_new import (
    SimpleUserRegistrationSerializer, UserProfileSerializer, TeacherProfileSerializer,
    StudentProfileUpdateSerializer, TeacherProfileUpdateSerializer,
    LanguageSerializer, MessageSerializer, ChatSerializer, GigSerializer
)
from core.models import User, Teacher
from django.conf import settings
from django.utils import timezone
from supabase import create_client

SUPABASE_URL = getattr(settings, "SUPABASE_URL", None)
SUPABASE_SERVICE_ROLE_KEY = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class SimpleRegistrationView(generics.CreateAPIView):
    """
    Simplified registration - only requires email, password, full_name, and role
    """
    serializer_class = SimpleUserRegistrationSerializer
    permission_classes = [AllowAny]

    @staticmethod
    def get_name_parts(full_name):
        parts = full_name.strip().split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return parts[0], ''

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # Create Supabase user
            response = supabase.auth.sign_up({
                "email": data['email'],
                "password": data['password'],
                'options': {'redirect_to': settings.BASE_URL_SIGNIN}
            })

            if not response.user:
                return Response(
                    {'error': 'Registration failed'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Split full name into first and last name
            first_name, last_name = self.get_name_parts(data['full_name'])

            # Update Supabase user metadata
            metadata = {
                'first_name': first_name,
                'last_name': last_name,
                'role': data['role']
            }
            
            supabase.auth.admin.update_user_by_id(
                response.user.id,
                {'user_metadata': metadata}
            )

            # Create Django User with minimal required fields
            user = User(
                id=response.user.id,
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                role=data['role'].upper(),  # Convert to uppercase to match User.Role choices
                is_active=True,
                created_at=timezone.now()
            )
            user.set_unusable_password()
            user.save()

            # Create UserProfile with minimal information
            profile = UserProfile.objects.create(
                user=user,
                role=data['role'],
                bio='',  # Empty initially
                city='',
                country='',
                postal_code='',
                status='',
                native_language='',
                learning_language=''
            )

            # If role is teacher, create empty TeacherProfile and Teacher instances
            if data['role'].upper() == User.Role.TEACHER:
                TeacherProfile.objects.create(
                    user_profile=profile,
                    qualification='',  # To be filled later
                    experience_years=0,
                    certificates=[],
                    about=''
                )

                Teacher.objects.create(
                    user=user,
                    bio='',
                    teaching_experience=0,
                    teaching_languages=[],
                    hourly_rate=0
                )

            return Response(
                {
                    'message': 'Registration successful. Please verify your email.',
                    'user_id': str(user.id),
                    'role': data['role']
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        return self.get_queryset().first()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current user's profile"""
        profile = self.get_object()
        if not profile:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], url_path='update-student')
    def update_student_profile(self, request):
        """Update student profile with student-specific fields"""
        profile = self.get_object()
        if not profile:
            return Response(
                {'error': 'Profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if profile.role.upper() != 'STUDENT':
            return Response(
                {'error': 'This endpoint is only for student profiles'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        partial = request.method == 'PATCH'
        serializer = StudentProfileUpdateSerializer(
            profile, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return the full profile data
        response_serializer = UserProfileSerializer(profile)
        return Response(response_serializer.data)

class TeacherProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher profiles
    """
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == User.Role.TEACHER:
            return TeacherProfile.objects.filter(user_profile__user=self.request.user)
        return TeacherProfile.objects.none()

    def get_object(self):
        return self.get_queryset().first()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get current teacher's profile"""
        if request.user.role != User.Role.TEACHER:
            return Response(
                {'error': 'Only teachers can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        teacher_profile = self.get_object()
        if not teacher_profile:
            return Response(
                {'error': 'Teacher profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(teacher_profile)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], url_path='update')
    def update_teacher_profile(self, request):
        """Update teacher profile with teacher-specific fields"""
        if request.user.role != User.Role.TEACHER:
            return Response(
                {'error': 'Only teachers can access this endpoint'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        teacher_profile = self.get_object()
        if not teacher_profile:
            return Response(
                {'error': 'Teacher profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        partial = request.method == 'PATCH'
        serializer = TeacherProfileUpdateSerializer(
            teacher_profile, 
            data=request.data, 
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return the full teacher profile data
        response_serializer = TeacherProfileSerializer(teacher_profile)
        return Response(response_serializer.data)

    @action(detail=False, methods=['get'])
    def list_teachers(self, request):
        """List all verified teachers (public endpoint)"""
        teacher_profiles = TeacherProfile.objects.filter(
            user_profile__user__is_active=True
        ).select_related('user_profile__user')
        
        serializer = self.get_serializer(teacher_profiles, many=True)
        return Response(serializer.data)

# Language management (unchanged)
class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]

# Chat and messaging (unchanged)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supabase_chats(request):
    user_id = str(request.user.id)
    result = supabase.table("chats").select("*").or_(f"participant1.eq.{user_id},participant2.eq.{user_id}").execute()
    return Response(result.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supabase_messages(request, chat_id):
    result = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return Response(result.data)

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(
            models.Q(participant1=self.request.user) | 
            models.Q(participant2=self.request.user)
        )

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            return Message.objects.filter(
                chat_id=chat_id,
                chat__in=Chat.objects.filter(
                    models.Q(participant1=self.request.user) | 
                    models.Q(participant2=self.request.user)
                )
            ).order_by('timestamp')
        return Message.objects.none()

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

# Gig management
class GigViewSet(viewsets.ModelViewSet):
    serializer_class = GigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            # Anyone can view gigs
            return Gig.objects.all().select_related('teacher__user_profile__user')
        else:
            # Only the teacher can modify their own gigs
            if self.request.user.role == User.Role.TEACHER:
                return Gig.objects.filter(teacher__user_profile__user=self.request.user)
            return Gig.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.TEACHER:
            raise serializers.ValidationError("Only teachers can create gigs")
        
        teacher_profile = TeacherProfile.objects.get(user_profile__user=self.request.user)
        serializer.save(teacher=teacher_profile)
