from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import models
from django.db.models import Q
from .models import UserProfile, TeacherProfile, Chat, Message, VoiceConversation, Gig
from .serializers import (
    UserProfileSerializer,
    TeacherProfileSerializer,
    TeacherProfileCreateSerializer,
    MessageSerializer,
    ComprehensiveTeacherProfileSerializer,
    ComprehensiveUserProfileSerializer,
    VoiceConversationSerializer,
    VoiceConversationCreateSerializer,
    TeacherSearchSerializer,
    GigSerializer,
)

from core.models import User
from django.conf import settings
from django.utils import timezone
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def supabase_chats(request):
    """Get all chats for the authenticated user with participant details.

    Uses Django ORM (Chat model) instead of direct Supabase REST API calls.
    This leverages select_related() to eliminate the N+1 query problem.
    """
    user = request.user
    role = request.query_params.get("role")

    # Build ORM query using the existing Chat model
    # The Chat model is already mapped to the 'chats' table (db_table = "chats")
    qs = Chat.objects.select_related("participant1", "participant2")
    if role == "student":
        qs = qs.filter(participant1=user)
    elif role == "teacher":
        qs = qs.filter(participant2=user)
    else:
        qs = qs.filter(models.Q(participant1=user) | models.Q(participant2=user))

    enhanced_chats = []
    for chat in qs:
        enhanced_chats.append(
            {
                "id": str(chat.id),
                "student_details": get_user_profile_details(chat.participant1),
                "teacher_details": get_user_profile_details(chat.participant2),
                "created_at": chat.created_at,
            }
        )

    return Response(enhanced_chats)


def get_user_profile_details(user):
    """Get essential user profile details (id, name, email, role, profile picture, created_at)"""
    try:
        # Get profile picture URL
        profile_picture = None
        if user.profile_picture:
            supabase_url = settings.SUPABASE_URL
            bucket_name = "user-uploads"
            profile_picture = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user.profile_picture}"

        # Return only essential fields
        return {
            "id": str(user.id),
            "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
            # 'email': user.email,
            "role": user.role,
            "profile_picture": profile_picture,
            # 'created_at': user.created_at
        }

    except Exception as e:
        return {
            "id": str(user.id),
            "name": "Unknown User",
            "email": "unknown@example.com",
            "role": "UNKNOWN",
            "profile_picture": None,
            "created_at": None,
            "error": f"Error getting profile details: {str(e)}",
        }


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def become_teacher(request):
    """Create a teacher profile for the authenticated user if one does not exist."""
    user = request.user
    # If already has teacher, return existing
    if user.has_teacher():
        # Try to return accounts TeacherProfile if available
        try:
            tp = user.profile.teacherprofile
            serializer = TeacherProfileSerializer(tp)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            # Fallback: return simple message
            return Response(
                {"detail": "Teacher profile already exists."}, status=status.HTTP_200_OK
            )

    # Create teacher profile (atomic)
    try:
        tp = user.create_teacher_profile()

        # Update roles to BOTH
        user.role = User.Role.BOTH
        user.save(update_fields=["role"])

        serializer = TeacherProfileSerializer(tp)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def become_student(request):
    """Create a student record for the authenticated user if one does not exist."""
    user = request.user
    if user.role in [User.Role.STUDENT, User.Role.BOTH]:
        return Response(
            {"detail": "Student profile already exists."}, status=status.HTTP_200_OK
        )

    try:
        # Just creating a UserProfile implies student capabilities.
        # If they don't have one, create it.
        if not hasattr(user, "profile"):
            UserProfile.objects.create(user=user)

        user.role = User.Role.BOTH
        user.save(update_fields=["role"])

        return Response(
            {
                "user_id": str(user.id),
                "detail": "Student capabilities added successfully.",
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def roles_status(request):
    """Return whether the authenticated user has teacher and/or student profiles.

    Source of truth is User.role — not the presence of a UserProfile record.
    A UserProfile is created as a safety net for all users, but it does NOT mean
    the user has the STUDENT role unless User.role is explicitly set to STUDENT or BOTH.
    """
    user = request.user

    # Use User.role as the single source of truth
    has_student = (
        user.role in [User.Role.STUDENT, User.Role.BOTH] if user.role else False
    )
    has_teacher = (
        user.role in [User.Role.TEACHER, User.Role.BOTH] if user.role else False
    )

    # Also check TeacherProfile existence (covers edge cases from older data)
    if not has_teacher:
        try:
            from accounts.models import TeacherProfile

            has_teacher = TeacherProfile.objects.filter(
                user_profile__user=user
            ).exists()
        except Exception:
            pass

    teacher_data = None
    student_data = None

    # Serialize student profile if applicable
    if has_student:
        try:
            if hasattr(user, "profile") and user.profile is not None:
                student_data = ComprehensiveUserProfileSerializer(user.profile).data
        except Exception:
            student_data = None

    # Serialize teacher profile if applicable
    if has_teacher:
        try:
            if hasattr(user, "profile") and user.profile is not None:
                teacher_profile = user.profile.teacherprofile
                teacher_data = ComprehensiveTeacherProfileSerializer(
                    teacher_profile
                ).data
        except Exception:
            teacher_data = None

    return Response(
        {
            "has_teacher": bool(has_teacher),
            "teacher_profile": teacher_data,
            "has_student": bool(has_student),
            "student_profile": student_data,
        }
    )


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)

    def get_object(self):
        # always returns the single profile for the current user
        return self.get_queryset().first()

    @action(detail=False, methods=["get", "put", "patch"], url_path="me")
    def me(self, request):
        profile = self.get_object()

        if request.method == "GET":
            # Use comprehensive serializer for GET to return all data
            serializer = ComprehensiveUserProfileSerializer(profile)
            return Response(serializer.data)

        # for PUT replace partial=False, for PATCH partial=True
        partial = request.method == "PATCH"
        # Use comprehensive serializer for updates
        serializer = ComprehensiveUserProfileSerializer(
            profile, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        updated_profile = serializer.save()

        # Return comprehensive profile data after update
        response_serializer = ComprehensiveUserProfileSerializer(updated_profile)
        return Response(
            {
                "message": "Profile updated successfully",
                "profile": response_serializer.data,
            }
        )


class TeacherPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TeacherProfileViewSet(viewsets.ModelViewSet):
    pagination_class = TeacherPagination

    def get_permissions(self):
        """
        Allow public access to list action, require authentication for others
        """
        if self.action == "list":
            # Public access for listing all teachers
            return []
        # Require authentication for all other actions
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "list":
            return TeacherSearchSerializer
        if self.action in ["create", "update", "partial_update"]:
            return TeacherProfileCreateSerializer
        return TeacherProfileSerializer

    def get_queryset(self):
        if self.action == "list":
            # Return active teacher profiles for public listing
            queryset = TeacherProfile.objects.select_related("user_profile__user").all()

            gig_category = self.request.query_params.get("gig_category")
            if gig_category:
                queryset = queryset.filter(
                    gigs__category=gig_category, gigs__status=Gig.Status.ACTIVE
                ).distinct()

            search = self.request.query_params.get("search")
            if search:
                queryset = queryset.filter(
                    Q(user_profile__user__first_name__icontains=search)
                    | Q(user_profile__user__last_name__icontains=search)
                    | Q(user_profile__user__email__icontains=search)
                )

            return queryset

        # Default: Filtered for the current user
        return TeacherProfile.objects.filter(user_profile__user=self.request.user)

    @action(detail=False, methods=["get", "patch"], url_path="my-profile")
    def my_profile(self, request):
        user = request.user

        # Ensure user is a teacher
        if user.role != User.Role.TEACHER:
            return Response(
                {"error": "This endpoint is only for teachers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # The profile is now automatically created by signals on user creation.
        # We just need to fetch it.
        try:
            teacher_profile = user.profile.teacherprofile
        except (AttributeError, UserProfile.DoesNotExist, TeacherProfile.DoesNotExist):
            return Response(
                {"error": "Teacher profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == "PATCH":
            # Use comprehensive serializer for updates
            serializer = ComprehensiveTeacherProfileSerializer(
                teacher_profile, data=request.data, partial=True
            )
            if serializer.is_valid():
                updated_profile = serializer.save()
                # Return comprehensive profile data after update
                response_serializer = ComprehensiveTeacherProfileSerializer(
                    updated_profile
                )
                return Response(
                    {
                        "message": "Profile updated successfully",
                        "profile": response_serializer.data,
                    }
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # For GET requests, return comprehensive data
        serializer = ComprehensiveTeacherProfileSerializer(teacher_profile)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        chat_id = self.request.query_params.get("chat_id")
        if chat_id:
            return Message.objects.filter(
                chat=chat_id, chat__participant1=user
            ) | Message.objects.filter(chat=chat_id, chat__participant2=user)
        # Return all messages user is part of (not recommended for prod)
        return Message.objects.filter(
            models.Q(chat__participant1=user) | models.Q(chat__participant2=user)
        )

    def perform_create(self, serializer):
        user = self.request.user
        chat_id = self.request.data.get("chat")
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            raise serializers.ValidationError("Chat not found")
        if user != chat.participant1 and user != chat.participant2:
            raise serializers.ValidationError("You are not a participant of this chat")
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
            raise serializers.ValidationError("You must be a teacher to create a gig.")

        # Check if teacher already has a gig with the same category
        category = serializer.validated_data.get("category")
        existing_gig = Gig.objects.filter(
            teacher=teacher_profile, category=category
        ).first()

        if existing_gig:
            category_display = dict(Gig.Category.choices).get(category, category)
            raise serializers.ValidationError(
                {
                    "exception_err": f"You already have a gig with the category '{category_display}'. "
                    f"Each teacher can only have one gig per category."
                }
            )

        serializer.save(teacher=teacher_profile)

    def perform_update(self, serializer):
        user = self.request.user
        try:
            teacher_profile = user.profile.teacherprofile
        except (AttributeError, TeacherProfile.DoesNotExist):
            raise serializers.ValidationError("You must be a teacher to update a gig.")

        # Check if teacher is trying to change category to one they already have
        category = serializer.validated_data.get("category")
        if category:
            existing_gig = (
                Gig.objects.filter(teacher=teacher_profile, category=category)
                .exclude(pk=serializer.instance.pk)
                .first()
            )

            if existing_gig:
                category_display = dict(Gig.Category.choices).get(category, category)
                raise serializers.ValidationError(
                    {
                        "exception_err": f"You already have a gig with the category '{category_display}'. "
                        f"Each teacher can only have one gig per category."
                    }
                )

        serializer.save(teacher=teacher_profile)

    @action(
        detail=False, methods=["get"], url_path="public", permission_classes=[AllowAny]
    )
    def public(self, request):
        """
        Get public gigs with optional filtering

        Query Parameters:
        - teacher_id: Filter by teacher user ID (UUID from teacher_details.id)
        - category: Filter by gig category
        - service_type: Filter by service type
        - min_price: Minimum price per session
        - max_price: Maximum price per session
        """
        # Base query - only active gigs
        gigs = Gig.objects.filter(status="active")

        # Filter by teacher user ID if provided
        teacher_id = request.query_params.get("teacher_id")
        if teacher_id:
            try:
                gigs = gigs.filter(teacher__user_profile__user__id=teacher_id)
            except Exception:
                # If invalid teacher_id format, return empty result
                gigs = gigs.none()

        # Filter by category if provided
        category = request.query_params.get("category")
        if category:
            gigs = gigs.filter(category__icontains=category)

        # Filter by service type if provided
        service_type = request.query_params.get("service_type")
        if service_type:
            gigs = gigs.filter(service_type__icontains=service_type)

        # Filter by price range if provided
        min_price = request.query_params.get("min_price")
        if min_price:
            try:
                gigs = gigs.filter(price_per_session__gte=float(min_price))
            except ValueError:
                pass  # Ignore invalid price format

        max_price = request.query_params.get("max_price")
        if max_price:
            try:
                gigs = gigs.filter(price_per_session__lte=float(max_price))
            except ValueError:
                pass  # Ignore invalid price format

        # Filter by session duration if provided
        min_duration = request.query_params.get("min_duration")
        if min_duration:
            try:
                gigs = gigs.filter(session_duration__gte=int(min_duration))
            except ValueError:
                pass

        max_duration = request.query_params.get("max_duration")
        if max_duration:
            try:
                gigs = gigs.filter(session_duration__lte=int(max_duration))
            except ValueError:
                pass

        # Search in title and description if provided
        search = request.query_params.get("search")
        if search:
            gigs = gigs.filter(
                Q(service_title__icontains=search)
                | Q(short_description__icontains=search)
                | Q(full_description__icontains=search)
            )

        # Order by created date (newest first) by default
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering in [
            "created_at",
            "-created_at",
            "price_per_session",
            "-price_per_session",
            "session_duration",
            "-session_duration",
        ]:
            gigs = gigs.order_by(ordering)
        else:
            gigs = gigs.order_by("-created_at")

        serializer = self.get_serializer(gigs, many=True)

        # Add metadata to response
        return Response(
            {
                "count": gigs.count(),
                "results": serializer.data,
                "filters_applied": {
                    "teacher_id": teacher_id,
                    "category": category,
                    "service_type": service_type,
                    "min_price": min_price,
                    "max_price": max_price,
                    "min_duration": min_duration,
                    "max_duration": max_duration,
                    "search": search,
                    "ordering": ordering,
                },
            }
        )

    @action(detail=True, methods=["get", "patch"], url_path="status")
    def status(self, request, pk=None):
        """Get or update the status of a specific gig"""
        gig = self.get_object()

        if request.method == "GET":
            # Get current status information
            return Response(
                {
                    "gig_id": gig.id,
                    "service_title": gig.service_title,
                    "current_status": gig.status,
                    "available_statuses": [
                        {"value": "active", "label": "Active - Available for booking"},
                        {
                            "value": "inactive",
                            "label": "Inactive - Temporarily unavailable",
                        },
                        {"value": "draft", "label": "Draft - Being prepared"},
                        {
                            "value": "suspended",
                            "label": "Suspended - Administrative action",
                        },
                    ],
                    "last_updated": gig.updated_at,
                }
            )

        elif request.method == "PATCH":
            # Update status
            new_status = request.data.get("status")

            if not new_status:
                return Response(
                    {"error": "Status field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate status value
            valid_statuses = ["active", "inactive", "draft", "suspended"]
            if new_status not in valid_statuses:
                return Response(
                    {
                        "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                        "valid_statuses": valid_statuses,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Store old status for response
            old_status = gig.status

            # Update the status
            gig.status = new_status
            gig.save(update_fields=["status", "updated_at"])

            return Response(
                {
                    "gig_id": gig.id,
                    "service_title": gig.service_title,
                    "old_status": old_status,
                    "new_status": new_status,
                    "updated_at": gig.updated_at,
                    "message": f'Gig status successfully updated from "{old_status}" to "{new_status}"',
                }
            )

    @action(detail=False, methods=["get"], url_path="status-summary")
    def status_summary(self, request):
        """Get a summary of all gig statuses for the teacher"""
        queryset = self.get_queryset()

        # Count gigs by status
        status_counts = {}
        for status_choice in ["active", "inactive", "draft", "suspended"]:
            count = queryset.filter(status=status_choice).count()
            status_counts[status_choice] = count

        # Get recent status changes (gigs updated in last 7 days)

        week_ago = timezone.now() - timedelta(days=7)
        recent_updates = queryset.filter(updated_at__gte=week_ago).order_by(
            "-updated_at"
        )[:10]

        recent_updates_data = []
        for gig in recent_updates:
            recent_updates_data.append(
                {
                    "id": gig.id,
                    "service_title": gig.service_title,
                    "current_status": gig.status,
                    "updated_at": gig.updated_at,
                }
            )

        return Response(
            {
                "total_gigs": queryset.count(),
                "status_breakdown": status_counts,
                "recent_updates": recent_updates_data,
                "available_actions": [
                    "View individual gig status: GET /accounts/gigs/{id}/status/",
                    "Update gig status: PATCH /accounts/gigs/{id}/status/",
                    "View this summary: GET /accounts/gigs/status-summary/",
                ],
            }
        )


class VoiceConversationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing OpenAI speech-to-speech voice conversations"""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return VoiceConversationCreateSerializer
        return VoiceConversationSerializer

    def get_queryset(self):
        """Return conversations for the authenticated user only"""
        return VoiceConversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Automatically assign the authenticated user to the conversation"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="by-language/(?P<language>[^/.]+)")
    def by_language(self, request, language=None):
        """Get conversations filtered by target language"""
        conversations = self.get_queryset().filter(target_language__iexact=language)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="by-type/(?P<conv_type>[^/.]+)")
    def by_type(self, request, conv_type=None):
        """Get conversations filtered by conversation type"""
        conversations = self.get_queryset().filter(conversation_type=conv_type)
        serializer = self.get_serializer(conversations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics of user's voice conversations"""
        queryset = self.get_queryset()

        # Basic statistics
        total_conversations = queryset.count()
        total_duration = (
            queryset.aggregate(total=models.Sum("duration_minutes"))["total"] or 0
        )

        # Conversations by language
        language_stats = {}
        for conv in queryset.values("target_language").annotate(
            count=models.Count("id")
        ):
            language_stats[conv["target_language"]] = conv["count"]

        # Conversations by type
        type_stats = {}
        for conv in queryset.values("conversation_type").annotate(
            count=models.Count("id")
        ):
            type_stats[conv["conversation_type"]] = conv["count"]

        # Recent activity (last 7 days)
        from datetime import timedelta

        week_ago = timezone.now() - timedelta(days=7)
        recent_conversations = queryset.filter(created_at__gte=week_ago).count()

        return Response(
            {
                "total_conversations": total_conversations,
                "total_duration_minutes": total_duration,
                "conversations_by_language": language_stats,
                "conversations_by_type": type_stats,
                "recent_conversations_last_7_days": recent_conversations,
                "available_conversation_types": [
                    {"value": choice[0], "label": choice[1]}
                    for choice in VoiceConversation.ConversationType.choices
                ],
            }
        )

    @action(detail=True, methods=["patch"])
    def add_feedback(self, request, pk=None):
        """Add or update AI feedback for a conversation"""
        conversation = self.get_object()
        feedback_data = request.data.get("ai_feedback", {})

        if not isinstance(feedback_data, dict):
            return Response(
                {"error": "ai_feedback must be a valid JSON object"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Merge new feedback with existing feedback
        existing_feedback = conversation.ai_feedback or {}
        existing_feedback.update(feedback_data)
        conversation.ai_feedback = existing_feedback
        conversation.save(update_fields=["ai_feedback"])

        serializer = self.get_serializer(conversation)
        return Response(
            {
                "message": "AI feedback updated successfully",
                "conversation": serializer.data,
            }
        )
