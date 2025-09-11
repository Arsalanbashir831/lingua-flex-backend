from rest_framework import generics, status, viewsets
from rest_framework import serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound
from django.db import transaction, models
from .models import UserProfile, TeacherProfile, Language, Chat, Message, VoiceConversation
from .serializers import (
    UserProfileSerializer, TeacherProfileSerializer,
    LanguageSerializer, TeacherProfileCreateSerializer, ChatSerializer, MessageSerializer,
    ComprehensiveTeacherProfileSerializer, ComprehensiveUserProfileSerializer,
    VoiceConversationSerializer, VoiceConversationCreateSerializer
)
from core.models import User, Teacher
from django.conf import settings
from django.utils import timezone
from supabase import create_client

SUPABASE_URL = getattr(settings, "SUPABASE_URL", None)
SUPABASE_SERVICE_ROLE_KEY = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

class UserRegistrationWithProfileSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField()
    role = serializers.CharField()
    bio = serializers.CharField(required=False, allow_blank=True)
    qualification = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False)
    certificates = serializers.JSONField(required=False)
    about = serializers.CharField(required=False, allow_blank=True)
    native_language = serializers.CharField(required=False, allow_blank=True)
    learning_language = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supabase_chats(request):
    """Get all chats for the authenticated user with participant details"""
    user_id = str(request.user.id)
    
    # Get chats from Supabase
    result = supabase.table("chats").select("*").or_(f"participant1.eq.{user_id},participant2.eq.{user_id}").execute()
    chats = result.data
    
    # Enhance chats with participant details
    enhanced_chats = []
    
    for chat in chats:
        try:
            # Get participant UUIDs
            participant1_id = chat.get('participant1')
            participant2_id = chat.get('participant2')
            
            # Initialize participant details
            student_details = None
            teacher_details = None
            
            # Get participant1 details
            if participant1_id:
                try:
                    participant1_user = User.objects.get(id=participant1_id)
                    student_details = get_user_profile_details(participant1_user)
                except User.DoesNotExist:
                    student_details = {
                        'id': participant1_id,
                        'error': 'User not found',
                        'role': 'UNKNOWN'
                    }
            
            # Get participant2 details
            if participant2_id:
                try:
                    participant2_user = User.objects.get(id=participant2_id)
                    teacher_details = get_user_profile_details(participant2_user)
                except User.DoesNotExist:
                    teacher_details = {
                        'id': participant2_id,
                        'error': 'User not found',
                        'role': 'UNKNOWN'
                    }
            
            # Create enhanced chat object
            enhanced_chat = {
                'id': chat.get('id'),
                # 'participant1': participant1_id,
                # 'participant2': participant2_id,
                'student_details': student_details,
                'teacher_details': teacher_details,
                'created_at': chat.get('created_at')
            }
            
            enhanced_chats.append(enhanced_chat)
            
        except Exception as e:
            # If there's an error with this chat, include it with error info
            enhanced_chat = chat.copy()
            enhanced_chat['error'] = f'Error processing chat: {str(e)}'
            enhanced_chats.append(enhanced_chat)
    
    return Response(enhanced_chats)

def get_user_profile_details(user):
    """Get essential user profile details (id, name, email, role, profile picture, created_at)"""
    try:
        # Get profile picture URL
        profile_picture = None
        if user.profile_picture:
            from django.conf import settings
            supabase_url = settings.SUPABASE_URL
            bucket_name = "user-uploads"
            profile_picture = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user.profile_picture}"
        
        # Return only essential fields
        return {
            'id': str(user.id),
            'name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            # 'email': user.email,
            'role': user.role,
            'profile_picture': profile_picture,
            # 'created_at': user.created_at
        }
        
    except Exception as e:
        return {
            'id': str(user.id),
            'name': 'Unknown User',
            'email': 'unknown@example.com',
            'role': 'UNKNOWN',
            'profile_picture': None,
            'created_at': None,
            'error': f'Error getting profile details: {str(e)}'
        }

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supabase_messages(request, chat_id):
    result = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return Response(result.data)

class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.filter(is_active=True)
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]

class RegisterWithProfileView(generics.CreateAPIView):
    serializer_class = UserRegistrationWithProfileSerializer
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
            # Check if user already exists in Django
            email = data['email']
            
            try:
                existing_user = User.objects.get(email=email)
                
                # Check if user is verified in Supabase
                try:
                    supabase_user = supabase.auth.admin.get_user_by_id(str(existing_user.id))
                    
                    # If user exists and is verified
                    if supabase_user.user and supabase_user.user.email_confirmed_at:
                        return Response(
                            {
                                'error': 'User already exists and is verified. Please login instead.',
                                'action': 'login'
                            },
                            status=status.HTTP_409_CONFLICT
                        )
                    
                    # If user exists but not verified, resend verification
                    else:
                        # Resend verification email
                        supabase.auth.resend({
                            'type': 'signup',
                            'email': email,
                            'options': {'email_redirect_to': settings.BASE_URL_SIGNIN}
                        })
                        
                        return Response(
                            {
                                'message': 'User exists but not verified. Verification email resent.',
                                'action': 'verify_email'
                            },
                            status=status.HTTP_200_OK
                        )
                        
                except Exception as supabase_error:
                    # If Supabase user doesn't exist but Django user does, create in Supabase
                    pass
                    
            except User.DoesNotExist:
                # User doesn't exist in Django, continue with registration
                pass

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
                'phone_number': data.get('phone_number'),
                'gender': data.get('gender'),
                'date_of_birth': data['date_of_birth'].isoformat() if data.get('date_of_birth') else None
            }
            
            supabase.auth.admin.update_user_by_id(
                response.user.id,
                {'user_metadata': metadata}
            )

            # Create Django User with role
            user = User(
                id=response.user.id,
                email=data['email'],
                first_name=first_name,
                last_name=last_name,
                phone_number=data.get('phone_number'),
                gender=data.get('gender'),
                date_of_birth=data.get('date_of_birth'),
                role=data['role'].upper(),  # Convert to uppercase to match User.Role choices
                is_active=True,
                created_at=timezone.now()
            )
            user.set_unusable_password()
            user.save()

            # Create UserProfile
            profile = UserProfile.objects.create(
                user=user,
                role=data['role'],
                bio=data.get('bio', ''),
                city=data.get('city', ''),
                country=data.get('country', ''),
                postal_code=data.get('postal_code', ''),
                status=data.get('status', ''),
                native_language=data.get('native_language', ''),
                learning_language=data.get('learning_language', '')
            )

            # If role is teacher, create TeacherProfile and Teacher
            if data['role'].upper() == User.Role.TEACHER:
                # Always create TeacherProfile, using defaults if fields are missing
                TeacherProfile.objects.create(
                    user_profile=profile,
                    qualification=data.get('qualification', ''),
                    experience_years=data.get('experience_years', 0),
                    certificates=data.get('certificates', []),
                    about=data.get('about', '')
                )

                # Optionally create Teacher model instance if needed
                Teacher.objects.create(
                    user=user,
                    bio=data.get('bio', ''),
                    teaching_experience=data.get('experience_years', 0),
                    teaching_languages=[],  # Can be updated later
                    hourly_rate=0  # Default value, can be updated later
                )

            return Response(
                {'message': 'Registration successful. Please verify your email.'},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

# class UserProfileViewSet(viewsets.ModelViewSet):
#     serializer_class = UserProfileSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return UserProfile.objects.filter(user=self.request.user)

#     def get_object(self):
#         return self.get_queryset().first()

from rest_framework.decorators import action
from rest_framework.response import Response

class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        # always returns the single profile for the current user
        return self.get_queryset().first()

    @action(detail=False, methods=['get', 'put', 'patch'], url_path='me')
    def me(self, request):
        profile = self.get_object()

        if request.method == 'GET':
            # Use comprehensive serializer for GET to return all data
            serializer = ComprehensiveUserProfileSerializer(profile)
            return Response(serializer.data)

        # for PUT replace partial=False, for PATCH partial=True
        partial = request.method == 'PATCH'
        # Use comprehensive serializer for updates
        serializer = ComprehensiveUserProfileSerializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_profile = serializer.save()
        
        # Return comprehensive profile data after update
        response_serializer = ComprehensiveUserProfileSerializer(updated_profile)
        return Response({
            'message': 'Profile updated successfully',
            'profile': response_serializer.data
        })




class TeacherProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TeacherProfileCreateSerializer
        return TeacherProfileSerializer

    def get_queryset(self):
        if self.action == 'list':
            return TeacherProfile.objects.all()
        elif self.action == 'my_profile':
            return TeacherProfile.objects.filter(
                user_profile__user=self.request.user,
                user_profile__role=User.Role.TEACHER
            )
        return TeacherProfile.objects.filter(user_profile__user=self.request.user)

    @action(detail=False, methods=['get', 'patch'], url_path='my-profile')
    def my_profile(self, request):
        user = request.user
        
        # Ensure user is a teacher
        if user.role != User.Role.TEACHER:
            return Response(
                {'error': 'This endpoint is only for teachers.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure user has UserProfile
        try:
            user_profile = user.profile
        except UserProfile.DoesNotExist:
            # Create UserProfile if it doesn't exist (for OAuth users)
            user_profile = UserProfile.objects.create(
                user=user,
                role=user.role,
                bio='',
                city='',
                country='',
                postal_code='',
                status='',
                native_language='',
                learning_language=''
            )
        
        # Ensure user has TeacherProfile
        try:
            teacher_profile = user_profile.teacherprofile
        except TeacherProfile.DoesNotExist:
            # Create TeacherProfile if it doesn't exist (for OAuth users)
            teacher_profile = TeacherProfile.objects.create(
                user_profile=user_profile,
                qualification='',
                experience_years=0,
                certificates=[],
                about=''
            )
        
        # Ensure user has Teacher model (for core functionality)
        try:
            teacher_model = user.teacher
        except Teacher.DoesNotExist:
            # Create Teacher if it doesn't exist (for OAuth users)
            teacher_model = Teacher.objects.create(
                user=user,
                bio='',
                teaching_experience=0,
                teaching_languages=[],
                hourly_rate=25.00
            )
        
        if request.method == 'PATCH':
            # Use comprehensive serializer for updates
            serializer = ComprehensiveTeacherProfileSerializer(teacher_profile, data=request.data, partial=True)
            if serializer.is_valid():
                updated_profile = serializer.save()
                # Return comprehensive profile data after update
                response_serializer = ComprehensiveTeacherProfileSerializer(updated_profile)
                return Response({
                    'message': 'Profile updated successfully',
                    'profile': response_serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # For GET requests, return comprehensive data
        serializer = ComprehensiveTeacherProfileSerializer(teacher_profile)
        return Response(serializer.data)


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from .models import Chat, Message, Gig
from .serializers import ChatSerializer, MessageSerializer, GigSerializer
from core.models import User

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(
            models.Q(participant1=user) | models.Q(participant2=user)
        )

    @action(detail=False, methods=['post'], url_path='start')
    def start_chat(self, request):
        user = request.user
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        if other_user == user:
            return Response({'error': 'Cannot start chat with yourself'}, status=status.HTTP_400_BAD_REQUEST)
        chat, created = Chat.objects.get_or_create(
            participant1=min(user, other_user, key=lambda u: u.id),
            participant2=max(user, other_user, key=lambda u: u.id)
        )
        serializer = self.get_serializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            return Message.objects.filter(chat_id=chat_id, chat__participant1=user) | Message.objects.filter(chat_id=chat_id, chat__participant2=user)
        # Return all messages user is part of (not recommended for prod)
        return Message.objects.filter(models.Q(chat__participant1=user) | models.Q(chat__participant2=user))

    def perform_create(self, serializer):
        user = self.request.user
        chat_id = self.request.data.get('chat')
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            raise serializers.ValidationError('Chat not found')
        if user != chat.participant1 and user != chat.participant2:
            raise serializers.ValidationError('You are not a participant of this chat')
        serializer.save(sender=user, chat=chat)

class GigViewSet(viewsets.ModelViewSet):
    serializer_class = GigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        try:
            teacher_profile = user.profile.teacherprofile
        except (AttributeError, TeacherProfile.DoesNotExist):
            return Gig.objects.none()
        return Gig.objects.filter(teacher=teacher_profile)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            teacher_profile = user.profile.teacherprofile
        except (AttributeError, TeacherProfile.DoesNotExist):
            raise serializers.ValidationError('You must be a teacher to create a gig.')
        serializer.save(teacher=teacher_profile)

    def perform_update(self, serializer):
        self.perform_create(serializer)

    @action(detail=False, methods=['get'], url_path='public', permission_classes=[AllowAny])
    def public(self, request):
        # Only return gigs with 'active' status for public viewing
        gigs = Gig.objects.filter(status='active')
        serializer = self.get_serializer(gigs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'], url_path='status')
    def status(self, request, pk=None):
        """Get or update the status of a specific gig"""
        gig = self.get_object()
        
        if request.method == 'GET':
            # Get current status information
            return Response({
                'gig_id': gig.id,
                'service_title': gig.service_title,
                'current_status': gig.status,
                'available_statuses': [
                    {'value': 'active', 'label': 'Active - Available for booking'},
                    {'value': 'inactive', 'label': 'Inactive - Temporarily unavailable'},
                    {'value': 'draft', 'label': 'Draft - Being prepared'},
                    {'value': 'suspended', 'label': 'Suspended - Administrative action'}
                ],
                'last_updated': gig.updated_at
            })
        
        elif request.method == 'PATCH':
            # Update status
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Status field is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate status value
            valid_statuses = ['active', 'inactive', 'draft', 'suspended']
            if new_status not in valid_statuses:
                return Response(
                    {
                        'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                        'valid_statuses': valid_statuses
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Store old status for response
            old_status = gig.status
            
            # Update the status
            gig.status = new_status
            gig.save(update_fields=['status', 'updated_at'])
            
            return Response({
                'gig_id': gig.id,
                'service_title': gig.service_title,
                'old_status': old_status,
                'new_status': new_status,
                'updated_at': gig.updated_at,
                'message': f'Gig status successfully updated from "{old_status}" to "{new_status}"'
            })

    @action(detail=False, methods=['get'], url_path='status-summary')
    def status_summary(self, request):
        """Get a summary of all gig statuses for the teacher"""
        queryset = self.get_queryset()
        
        # Count gigs by status
        status_counts = {}
        for status_choice in ['active', 'inactive', 'draft', 'suspended']:
            count = queryset.filter(status=status_choice).count()
            status_counts[status_choice] = count
        
        # Get recent status changes (gigs updated in last 7 days)
        from django.utils import timezone
        from datetime import timedelta
        
        week_ago = timezone.now() - timedelta(days=7)
        recent_updates = queryset.filter(updated_at__gte=week_ago).order_by('-updated_at')[:10]
        
        recent_updates_data = []
        for gig in recent_updates:
            recent_updates_data.append({
                'id': gig.id,
                'service_title': gig.service_title,
                'current_status': gig.status,
                'updated_at': gig.updated_at
            })
        
        return Response({
            'total_gigs': queryset.count(),
            'status_breakdown': status_counts,
            'recent_updates': recent_updates_data,
            'available_actions': [
                'View individual gig status: GET /accounts/gigs/{id}/status/',
                'Update gig status: PATCH /accounts/gigs/{id}/status/',
                'View this summary: GET /accounts/gigs/status-summary/'
            ]
        })

class VoiceConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing OpenAI speech-to-speech voice conversations"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VoiceConversationCreateSerializer
        return VoiceConversationSerializer
    
    def get_queryset(self):
        """Return conversations for the authenticated user only"""
        return VoiceConversation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Automatically assign the authenticated user to the conversation"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='by-language/(?P<language>[^/.]+)')
    def by_language(self, request, language=None):
        """Get conversations filtered by target language"""
        conversations = self.get_queryset().filter(target_language__iexact=language)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='by-type/(?P<conv_type>[^/.]+)')
    def by_type(self, request, conv_type=None):
        """Get conversations filtered by conversation type"""
        conversations = self.get_queryset().filter(conversation_type=conv_type)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics of user's voice conversations"""
        queryset = self.get_queryset()
        
        # Basic statistics
        total_conversations = queryset.count()
        total_duration = queryset.aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0
        
        # Conversations by language
        language_stats = {}
        for conv in queryset.values('target_language').annotate(count=models.Count('id')):
            language_stats[conv['target_language']] = conv['count']
        
        # Conversations by type
        type_stats = {}
        for conv in queryset.values('conversation_type').annotate(count=models.Count('id')):
            type_stats[conv['conversation_type']] = conv['count']
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_conversations = queryset.filter(created_at__gte=week_ago).count()
        
        return Response({
            'total_conversations': total_conversations,
            'total_duration_minutes': total_duration,
            'conversations_by_language': language_stats,
            'conversations_by_type': type_stats,
            'recent_conversations_last_7_days': recent_conversations,
            'available_conversation_types': [
                {'value': choice[0], 'label': choice[1]} 
                for choice in VoiceConversation.ConversationType.choices
            ]
        })
    
    @action(detail=True, methods=['patch'])
    def add_feedback(self, request, pk=None):
        """Add or update AI feedback for a conversation"""
        conversation = self.get_object()
        feedback_data = request.data.get('ai_feedback', {})
        
        if not isinstance(feedback_data, dict):
            return Response(
                {'error': 'ai_feedback must be a valid JSON object'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Merge new feedback with existing feedback
        existing_feedback = conversation.ai_feedback or {}
        existing_feedback.update(feedback_data)
        conversation.ai_feedback = existing_feedback
        conversation.save(update_fields=['ai_feedback'])
        
        serializer = self.get_serializer(conversation)
        return Response({
            'message': 'AI feedback updated successfully',
            'conversation': serializer.data
        })