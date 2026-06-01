from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction, models
from django.conf import settings
import logging


from .models import User
from .serializers import (
    UserSerializer,
    SyncSupabaseUserSerializer,
    SetUserRoleSerializer,
    GoogleOAuthUserSerializer,
)
from accounts.models import UserProfile, TeacherProfile
from core.supabase_client import get_admin_client
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)


class SyncSupabaseUserView(APIView):
    """
    Sync Supabase authenticated user to Django database.

    POST /api/auth/sync/
    {
        "access_token": "supabase_access_token",
        "role": "STUDENT" | "TEACHER"  # optional
    }
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SyncSupabaseUserSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"[sync] Invalid request data: {serializer.errors}")
            return Response(
                {
                    "success": False,
                    "error": "Invalid sync data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        access_token = data["access_token"]
        provided_role = data.get("role")
        logger.info(f"[sync] Starting sync. provided_role={provided_role}")

        try:
            # Step 1: Validate token with Supabase
            logger.info("[sync] Calling get_admin_client().auth.get_user()")
            supabase_user = get_admin_client().auth.get_user(access_token)
            logger.info(f"[sync] Supabase response: user={supabase_user.user}")

            if not supabase_user.user:
                logger.error("[sync] Supabase returned no user for this token")
                return Response(
                    {"success": False, "error": "Invalid access token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user_data = supabase_user.user
            email = user_data.email
            supabase_id = str(user_data.id)
            logger.info(f"[sync] Supabase user: email={email}, id={supabase_id}")

            # Step 2: Extract name from user metadata
            user_metadata = user_data.user_metadata or {}
            first_name = user_metadata.get("first_name") or user_metadata.get(
                "given_name", ""
            )
            last_name = user_metadata.get("last_name") or user_metadata.get(
                "family_name", ""
            )
            full_name = user_metadata.get("full_name") or user_metadata.get("name", "")

            if not first_name and not last_name and full_name:
                name_parts = full_name.strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

            logger.info(
                f"[sync] Extracted name: first={first_name!r}, last={last_name!r}"
            )

            # Step 3: Determine auth provider
            google_id = None
            is_google_login = False
            for identity in user_data.identities or []:
                if identity.provider == "google":
                    google_id = identity.id
                    is_google_login = True
                    break

            logger.info(
                f"[sync] is_google_login={is_google_login}, google_id={google_id}"
            )

            with transaction.atomic():
                user = None
                created = False

                try:
                    user = User.objects.get(
                        models.Q(email=email) | models.Q(id=supabase_id)
                    )
                    logger.info(f"[sync] Found existing user: id={user.id}")

                    if is_google_login and not user.is_oauth_user:
                        user.is_oauth_user = True
                        user.auth_provider = User.AuthProvider.GOOGLE
                        user.google_id = google_id
                        user.email_verified = True
                        user.save()
                        logger.info(
                            "[sync] Updated existing user with Google OAuth info"
                        )

                except User.DoesNotExist:
                    logger.info(
                        f"[sync] User not found, creating new. google_id={google_id!r}"
                    )
                    try:
                        user = User.objects.create_oauth_user(
                            id=supabase_id,
                            email=email,
                            first_name=first_name,
                            last_name=last_name,
                            role=provided_role,
                            auth_provider=User.AuthProvider.GOOGLE
                            if is_google_login
                            else User.AuthProvider.EMAIL,
                            google_id=google_id,
                        )
                        created = True
                        logger.info(
                            f"[sync] Created new user: id={user.id}, email={user.email}"
                        )
                    except Exception as create_err:
                        logger.error(
                            f"[sync] Failed to create user: {create_err}", exc_info=True
                        )
                        raise

                # Step 4: Create profiles if role is already known
                if user.role and not hasattr(user, "profile"):
                    try:
                        user_profile = UserProfile.objects.create(user=user, bio="")
                        if user.role == User.Role.TEACHER:
                            TeacherProfile.objects.create(user_profile=user_profile)
                        logger.info(f"[sync] Created profiles for role={user.role}")
                    except Exception as profile_err:
                        logger.error(
                            f"[sync] Profile creation failed: {profile_err}",
                            exc_info=True,
                        )

                # Self-healing auto-resolve role based on existing profiles
                has_teacher = TeacherProfile.objects.filter(
                    user_profile__user=user
                ).exists()
                has_student = UserProfile.objects.filter(user=user).exists()

                if has_teacher and has_student and user.role != User.Role.BOTH:
                    user.role = User.Role.BOTH
                    user.save(update_fields=["role"])
                    logger.info(
                        "[sync] Self-healed role to BOTH because both profiles exist"
                    )
                elif user.role is None and has_teacher:
                    user.role = User.Role.TEACHER
                    user.save(update_fields=["role"])
                    logger.info(
                        "[sync] Self-healed role to TEACHER based on existing TeacherProfile"
                    )

            requires_role_selection = user.role is None
            logger.info(
                f"[sync] Done. created={created}, requires_role_selection={requires_role_selection}"
            )

            user_serializer = GoogleOAuthUserSerializer(user)
            return Response(
                {
                    "success": True,
                    "message": f"User {'registered' if created else 'synced'} successfully",
                    "user": user_serializer.data,
                    "requires_role_selection": requires_role_selection,
                },
                status=status.HTTP_200_OK,
            )

        except AuthApiError as e:
            logger.error(f"[sync] Supabase auth error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": f"Authentication error: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"[sync] Unexpected error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": f"Sync failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SetUserRoleView(APIView):
    """
    Set user role post-signup and initialize profiles.

    POST /api/auth/set-role/
    {
        "role": "STUDENT" | "TEACHER"
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetUserRoleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        role = serializer.validated_data["role"]

        if user.role:
            return Response(
                {"error": f"User already has a role assigned: {user.role}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user.role = role
                user.save()

                # Create profiles minimally
                user_profile, created = UserProfile.objects.get_or_create(
                    user=user, defaults={"bio": ""}
                )

                if role == User.Role.TEACHER:
                    TeacherProfile.objects.get_or_create(user_profile=user_profile)

            return Response(
                {
                    "success": True,
                    "message": f"Role set to {role} and profiles initialized.",
                    "user": GoogleOAuthUserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error in SetUserRoleView: {e}")
            return Response(
                {"error": f"Failed to set role: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfilePictureUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        user = request.user
        file_obj = request.FILES.get("profile_picture")
        if not file_obj:
            return Response(
                {"error": "No profile_picture file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        folder = f"user_{user.id}"
        filename = file_obj.name
        storage_key = f"{folder}/{filename}"

        supabase = get_admin_client()

        try:
            # Delete previous profile picture if exists
            if user.profile_picture and user.profile_picture.name:
                try:
                    # Get the file path string from ImageFieldFile
                    previous_file_path = user.profile_picture.name
                    supabase.storage.from_("user-uploads").remove([previous_file_path])
                    # print(f"Previous profile picture deletion result: {delete_res}")
                except Exception as delete_error:
                    print(
                        f"Warning: Could not delete previous profile picture: {delete_error}"
                    )
                    # Continue with upload even if deletion fails

            file_bytes = file_obj.read()

            # Upload to Supabase Storage
            res = supabase.storage.from_("user-uploads").upload(
                storage_key, file_bytes, {"content-type": file_obj.content_type}
            )
            if isinstance(res, dict) and res.get("error"):
                return Response(
                    {"error": res["error"]["message"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set profile_picture field to the storage key or URL
            user.profile_picture = storage_key  # or construct a full URL if needed
            user.save(update_fields=["profile_picture"])

            # No local file to delete since file is read directly from upload

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # return Response(data, status=status.HTTP_200_OK)

        # except Exception as e:
        #     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserProfilePictureGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile_picture_key = user.profile_picture
        if not profile_picture_key:
            return Response(
                {"error": "User has no profile picture."},
                status=status.HTTP_404_NOT_FOUND,
            )

        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"

        # Construct public URL (assuming bucket is public or using signed URLs would require more implementation)
        image_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{profile_picture_key}"

        return Response({"profile_picture_url": image_url}, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    Lightweight health-check endpoint for CI/CD pipeline verification and uptime monitoring.

    GET /api/health/
    Returns HTTP 200 if the server is up and the database is reachable.
    Returns HTTP 503 if the database is unavailable.

    This endpoint requires no authentication so that the GitHub Actions workflow
    can poll it immediately after a deploy to confirm the server is live.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No auth overhead on health checks

    def get(self, request):
        from django.db import connection

        try:
            # Perform a lightweight DB connectivity check
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as exc:
            logger.error("Health check DB probe failed: %s", exc)
            return Response(
                {"status": "unhealthy", "detail": "Database connection failed."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "ok",
                "database": "reachable",
            },
            status=status.HTTP_200_OK,
        )
