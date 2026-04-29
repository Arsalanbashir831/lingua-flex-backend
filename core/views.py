from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction, models
from django.conf import settings
import logging

# Temporary fix for ZoomClient import issue
try:
    from zoomus import ZoomClient

    # Initialize Zoom client only if credentials are configured
    zoom_client = None
    if (
        hasattr(settings, "ZOOM_API_KEY")
        and settings.ZOOM_API_KEY
        and hasattr(settings, "ZOOM_API_SECRET")
        and settings.ZOOM_API_SECRET
        and hasattr(settings, "ZOOM_ACCOUNT_ID")
        and settings.ZOOM_ACCOUNT_ID
    ):
        try:
            zoom_client = ZoomClient(
                settings.ZOOM_ACCOUNT_ID,
                settings.ZOOM_API_KEY,
                settings.ZOOM_API_SECRET,
            )
        except Exception as e:
            print(f"Warning: Could not initialize ZoomClient: {e}")
            zoom_client = None
except ImportError:
    print(
        "Warning: zoomus library not installed or outdated. Zoom functionality will be disabled."
    )
    zoom_client = None
from .models import (
    User,
    Teacher,
)
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    GoogleOAuthInitiateSerializer,
    GoogleOAuthCallbackSerializer,
    GoogleOAuthUserSerializer,
)
from accounts.models import UserProfile, TeacherProfile
from supabase import create_client
from gotrue.errors import AuthApiError

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
logger = logging.getLogger(__name__)


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
                {
                    "success": False,
                    "error": "Invalid data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        role = data.get("role")  # Optional now
        redirect_url = data.get("redirect_url", settings.BASE_URL_SIGNIN)

        try:
            # Generate OAuth URL through Supabase
            # The frontend will redirect user to this URL
            oauth_url = f"{settings.SUPABASE_URL}/auth/v1/authorize"
            params = {
                "provider": "google",
                "redirect_to": redirect_url,
                "scopes": "openid email profile",
            }

            # Build full OAuth URL
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_oauth_url = f"{oauth_url}?{param_string}"

            response_data = {
                "success": True,
                "oauth_url": full_oauth_url,
                "message": "Redirect user to oauth_url to complete Google authentication",
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error initiating Google OAuth: {e}")
            return Response(
                {"success": False, "error": f"Failed to initiate OAuth: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                {
                    "success": False,
                    "error": "Invalid callback data",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")
        provided_role = data.get("role")  # May be None for existing users

        try:
            # Get user data from Supabase using the access token
            supabase_user = supabase.auth.get_user(access_token)

            if not supabase_user.user:
                return Response(
                    {"success": False, "error": "Invalid access token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            user_data = supabase_user.user
            email = user_data.email
            supabase_id = user_data.id

            # Extract name from user metadata or app_metadata
            user_metadata = user_data.user_metadata or {}
            first_name = user_metadata.get("first_name") or user_metadata.get(
                "given_name", ""
            )
            last_name = user_metadata.get("last_name") or user_metadata.get(
                "family_name", ""
            )
            full_name = user_metadata.get("full_name") or user_metadata.get("name", "")

            # If we don't have separate first/last names, try to split full name
            if not first_name and not last_name and full_name:
                name_parts = full_name.strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Get Google ID from provider data
            google_id = None
            for identity in user_data.identities or []:
                if identity.provider == "google":
                    google_id = identity.id
                    break

            with transaction.atomic():
                # Check if user already exists
                user = None
                created = False
                is_existing_user_login = False

                try:
                    # Try to find existing user by email or Supabase ID
                    user = User.objects.get(
                        models.Q(email=email) | models.Q(id=supabase_id)
                    )
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
                                "success": False,
                                "error": "Role is required for new user registration",
                                "requires_role_selection": True,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user = User.objects.create_oauth_user(
                        id=supabase_id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        role=provided_role,
                        auth_provider=User.AuthProvider.GOOGLE,
                        google_id=google_id,
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
                        bio="",
                        city="",
                        country="",
                        postal_code="",
                        status="",
                        native_language="",
                        learning_language="",
                    )

                    # Only create additional models for TEACHERS (same as RegisterWithProfileView)
                    if user_role == User.Role.TEACHER:
                        # Create TeacherProfile model (accounts model)
                        TeacherProfile.objects.create(
                            user_profile=user_profile,
                            qualification="",
                            experience_years=0,
                            certificates=[],
                            about="",
                        )

                        # Create Teacher model (core model) - for booking system
                        Teacher.objects.create(
                            user=user,
                            bio="",  # Will be filled in profile completion
                            teaching_experience=0,
                            teaching_languages=[],
                            hourly_rate=0,  # Default value, can be updated later
                        )

                    # For STUDENTS: Only UserProfile is created (no Student model)

            # Serialize user data for response
            user_serializer = GoogleOAuthUserSerializer(user)

            return Response(
                {
                    "success": True,
                    "message": f"User {'registered' if created else 'logged in'} successfully via Google",
                    "user": user_serializer.data,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "created": created,
                    "is_existing_user_login": is_existing_user_login,
                    "requires_profile_completion": created,  # New users need to complete profile
                    "flow_type": "registration" if created else "login",
                },
                status=status.HTTP_200_OK,
            )

        except AuthApiError as e:
            logger.error(f"Supabase auth error: {e}")
            return Response(
                {"success": False, "error": f"Authentication error: {str(e)}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"Error in Google OAuth callback: {e}")
            return Response(
                {"success": False, "error": f"OAuth callback failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_data = serializer.validated_data
                email = user_data["email"]
                password = user_data["password"]
                username = user_data.get("username", "")
                first_name = user_data.get("first_name", "")
                last_name = user_data.get("last_name", "")
                phone_number = user_data.get("phone_number", "")
                gender = user_data.get("gender", "")
                date_of_birth = user_data.get("date_of_birth", None)
                role = user_data.get(
                    "role", "STUDENT"
                )  # Default to STUDENT if not provided

                response = supabase.auth.sign_up(
                    {
                        "email": email,
                        "password": password,
                        "options": {"redirect_to": settings.BASE_URL_SIGNIN},
                    }
                )
                if response.user:
                    supabase.auth.admin.update_user_by_id(
                        response.user.id,
                        {
                            "user_metadata": {
                                "username": username,
                                "first_name": first_name,
                                "last_name": last_name,
                                "phone_number": phone_number,
                                "gender": gender,
                                "date_of_birth": date_of_birth.isoformat()
                                if date_of_birth
                                else None,
                            }
                        },
                    )
                    # Create the user
                    with transaction.atomic():
                        user_model = User(
                            id=response.user.id,
                            email=email,
                            username=username,
                            first_name=first_name,
                            last_name=last_name,
                            phone_number=phone_number,
                            gender=gender,
                            date_of_birth=date_of_birth,
                            role=role,
                            is_active=True,
                        )
                        user_model.set_unusable_password()
                        user_model.save()

                        # If role is teacher, create the teacher profile
                        if role == "TEACHER":
                            Teacher.objects.create(
                                user=user_model,
                                bio=user_data.get("bio", ""),
                                teaching_experience=user_data["years_of_experience"],
                                teaching_languages=[],  # Can be updated later
                                hourly_rate=0,  # Default value, can be updated later
                            )

                    return Response(
                        {"message": "User registered successfully"},
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Registration failed"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            response = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as e:
            return Response(
                {"error": "Failed to login. " + str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if hasattr(response, "error") and response.error:
            return Response(
                {"error": str(response.error)}, status=status.HTTP_400_BAD_REQUEST
            )

        user = response.user
        if not user:
            return Response(
                {"error": "Invalid login credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Get the user from Django database to fetch the role
        try:
            django_user = User.objects.get(id=user.id)
            user_role = django_user.role
        except User.DoesNotExist:
            # If user doesn't exist in Django database, default to STUDENT
            user_role = User.Role.STUDENT

        return Response(
            {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {"email": user.email, "id": user.id, "role": user_role},
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Trigger password reset email through Supabase
            supabase.auth.reset_password_for_email(
                email, options={"redirect_to": settings.BASE_URL_RESET_PASSWORD}
            )
            return Response(
                {"message": "Password reset email sent"}, status=status.HTTP_200_OK
            )
        except AuthApiError as e:
            # Handle rate limit error specifically
            if "rate limit" in str(e).lower():
                return Response(
                    {
                        "error": "Too many requests. Please wait a moment before trying again."
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Failed to send password reset email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetConfirmView(APIView):
    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        if not token or not new_password:
            return Response(
                {"error": "Token and new password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import requests
        from django.conf import settings

        project_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
        api_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or getattr(
            settings, "SUPABASE_ANON_KEY", ""
        )
        if not project_url or not api_key:
            return Response(
                {"error": "Supabase configuration missing."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        url = f"{project_url}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": api_key,
            "Content-Type": "application/json",
        }
        payload = {"password": new_password}

        try:
            resp = requests.put(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return Response(
                    {"error": resp.json().get("message", "Failed to update password")},
                    status=resp.status_code,
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """
    Allows an authenticated user (student or teacher) to update their password.
    Requires the current password for verification before applying the new one.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")

        if not current_password or not new_password:
            return Response(
                {"error": "current_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current_password == new_password:
            return Response(
                {"error": "New password must be different from the current password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        # Step 1: Verify current password via Supabase sign-in
        # This ensures the user actually knows their current password
        try:
            auth_response = supabase.auth.sign_in_with_password(
                {"email": user.email, "password": current_password}
            )
        except AuthApiError as e:
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Authentication failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Step 2: Update password using the access token returned from the sign-in
        # This is the most reliable way to update a password for the current user
        try:
            # We create a temporary client with the bearer token from the verification sign-in
            temp_supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,  # Use anon key but provide user's specific session
            )
            temp_supabase.auth.set_session(
                auth_response.session.access_token, auth_response.session.refresh_token
            )

            temp_supabase.auth.update_user({"password": new_password})

            return Response(
                {"message": "Password updated successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to update password: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationView(APIView):
    """
    Resend email verification link for unverified users
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if user exists in Django database
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": "User with this email does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Try to resend verification email directly
            # Supabase will handle checking if user exists and is unverified
            try:
                resend_response = supabase.auth.resend(
                    {
                        "type": "signup",
                        "email": email,
                        "options": {
                            "email_redirect_to": settings.BASE_URL_SIGNIN,
                        },
                    }
                )

                return Response(
                    {
                        "message": "Verification email has been resent successfully, if user is not verified.",
                        "email": email,
                        #'instructions': 'Please check your email and click the verification link to activate your account.'
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as supabase_error:
                error_message = str(supabase_error)

                # Handle specific Supabase errors
                if "user not found" in error_message.lower():
                    return Response(
                        {
                            "error": "User with this email does not exist in the authentication system"
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
                elif (
                    "already confirmed" in error_message.lower()
                    or "already verified" in error_message.lower()
                ):
                    return Response(
                        {
                            "error": "User is already verified",
                            "message": "Your email is already verified. You can log in directly.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {
                            "error": f"Failed to resend verification email: {error_message}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = supabase.auth.refresh_session(refresh_token)
            if (
                data.session
                and data.session.access_token
                and data.session.refresh_token
            ):
                return Response(
                    {
                        "access_token": data.session.access_token,
                        "refresh_token": data.session.refresh_token,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Failed to refresh token"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

        supabase = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )

        try:
            # Delete previous profile picture if exists
            if user.profile_picture and user.profile_picture.name:
                try:
                    # Get the file path string from ImageFieldFile
                    previous_file_path = user.profile_picture.name
                    delete_res = supabase.storage.from_("user-uploads").remove(
                        [previous_file_path]
                    )
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
