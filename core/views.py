from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
import uuid
import os
from datetime import datetime
# Temporary fix for ZoomClient import issue
try:
    from zoomus import ZoomClient
    # Initialize Zoom client only if credentials are configured
    zoom_client = None
    if (hasattr(settings, 'ZOOM_API_KEY') and settings.ZOOM_API_KEY and 
        hasattr(settings, 'ZOOM_API_SECRET') and settings.ZOOM_API_SECRET and 
        hasattr(settings, 'ZOOM_ACCOUNT_ID') and settings.ZOOM_ACCOUNT_ID):
        try:
            zoom_client = ZoomClient(settings.ZOOM_ACCOUNT_ID, settings.ZOOM_API_KEY, settings.ZOOM_API_SECRET)
        except Exception as e:
            print(f"Warning: Could not initialize ZoomClient: {e}")
            zoom_client = None
except ImportError:
    print("Warning: zoomus library not installed or outdated. Zoom functionality will be disabled.")
    zoom_client = None
from .models import (
    User, File, Student, Teacher, TeacherCertificate,
    TimeSlot, TeacherGig, Session, SessionBilling, AIConversation
)
from .serializers import (
    UserRegistrationSerializer, UserSerializer, FileSerializer,
    TeacherProfileSerializer, StudentProfileSerializer,
    TeacherGigSerializer, SessionSerializer, SessionBillingSerializer,
    AIConversationSerializer, TeacherCertificateSerializer,
    TimeSlotSerializer
)
from supabase import create_client
from gotrue.errors import AuthApiError

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user_data = serializer.validated_data
                email = user_data['email']
                password = user_data['password']
                username = user_data.get('username', '')
                first_name = user_data.get('first_name', '')
                last_name = user_data.get('last_name', '')
                phone_number = user_data.get('phone_number', '')
                gender = user_data.get('gender', '')
                date_of_birth = user_data.get('date_of_birth', None)
                role = user_data.get('role', 'STUDENT')  # Default to STUDENT if not provided

                response = supabase.auth.sign_up({"email": email, "password": password,'options': {'redirect_to': settings.BASE_URL_SIGNIN }})
                if response.user:
                    supabase.auth.admin.update_user_by_id(response.user.id, {'user_metadata': {
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone_number': phone_number,
                        'gender': gender,
                        'date_of_birth': date_of_birth.isoformat() if date_of_birth else None                        
                        
                    }})
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
                            is_active=True
                        )
                        user_model.set_unusable_password()
                        user_model.save()

                        # If role is teacher, create the teacher profile
                        if role == 'TEACHER':
                            Teacher.objects.create(
                                user=user_model,
                                bio=user_data.get('bio', ''),
                                teaching_experience=user_data['years_of_experience'],
                                teaching_languages=[],  # Can be updated later
                                hourly_rate=0  # Default value, can be updated later
                            )

                    return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
                else:
                    return Response({'error': 'Registration failed'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            response = supabase.auth.sign_in_with_password({'email': email, 'password': password})
            if response.user:
                return Response({
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = supabase.auth.sign_in_with_password(
                {'email': email, 'password': password}
            )
        except Exception as e:
            return Response({'error': 'Failed to login. ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(response, 'error') and response.error:
            return Response({'error': str(response.error)}, status=status.HTTP_400_BAD_REQUEST)

        user = response.user
        if not user:
            return Response({'error': 'Invalid login credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get the user from Django database to fetch the role
        try:
            django_user = User.objects.get(id=user.id)
            user_role = django_user.role
        except User.DoesNotExist:
            # If user doesn't exist in Django database, default to STUDENT
            user_role = User.Role.STUDENT

        return Response({
            'access_token': response.session.access_token,
            'refresh_token': response.session.refresh_token,
            'user': {
                'email': user.email, 
                'id': user.id,
                'role': user_role
            }
        }, status=status.HTTP_200_OK)



class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            response = supabase.auth.reset_password_for_email(email)
            if response:
                return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to send password reset email'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# resetpass_url ='http://localhost:3000/reset-password'
class PasswordResetView(APIView):
  
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger password reset email through Supabase
        response = supabase.auth.reset_password_for_email(email, options={'redirect_to': settings.BASE_URL_RESET_PASSWORD})

        if hasattr(response, 'error') and response.error:
            return Response({'error': str(response.error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)




class PasswordResetConfirmView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not token or not new_password:
            return Response({'error': 'Token and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        import requests
        from django.conf import settings

        project_url = getattr(settings, 'SUPABASE_URL', '').rstrip('/')
        api_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '') or getattr(settings, 'SUPABASE_ANON_KEY', '')
        if not project_url or not api_key:
            return Response({'error': 'Supabase configuration missing.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        url = f'{project_url}/auth/v1/user'
        headers = {
            'Authorization': f'Bearer {token}',
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
        payload = {'password': new_password}

        try:
            resp = requests.put(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return Response({'error': resp.json().get('message', 'Failed to update password')}, status=resp.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)


class ResendVerificationView(APIView):
    """
    Resend email verification link for unverified users
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if user exists in Django database
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User with this email does not exist'}, 
                    status=status.HTTP_404_NOT_FOUND
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
                        'message': 'Verification email has been resent successfully, if user is not verified.',
                        'email': email,
                        #'instructions': 'Please check your email and click the verification link to activate your account.'
                    }, 
                    status=status.HTTP_200_OK
                )
                
            except Exception as supabase_error:
                error_message = str(supabase_error)
                
                # Handle specific Supabase errors
                if 'user not found' in error_message.lower():
                    return Response(
                        {'error': 'User with this email does not exist in the authentication system'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                elif 'already confirmed' in error_message.lower() or 'already verified' in error_message.lower():
                    return Response(
                        {
                            'error': 'User is already verified', 
                            'message': 'Your email is already verified. You can log in directly.'
                        }, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'error': f'Failed to resend verification email: {error_message}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        except Exception as e:
            return Response(
                {'error': f'Unexpected error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = supabase.auth.api.exchange_refresh_token(refresh_token)
            if response.access_token:
                return Response({'access_token': response.access_token}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'refresh_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = supabase.auth.refresh_session(refresh_token)
            if data.session and data.session.access_token and data.session.refresh_token:
                return Response({
                    'access_token': data.session.access_token,
                    'refresh_token': data.session.refresh_token
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfilePictureUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]


    def post(self, request, *args, **kwargs):
        user = request.user
        file_obj = request.FILES.get('profile_picture')
        if not file_obj:
            return Response({"error": "No profile_picture file provided."}, status=status.HTTP_400_BAD_REQUEST)

        folder = f"user_{user.id}"
        filename = file_obj.name
        storage_key = f"{folder}/{filename}"

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

        try:
            # Delete previous profile picture if exists
            if user.profile_picture and user.profile_picture.name:
                try:
                    # Get the file path string from ImageFieldFile
                    previous_file_path = user.profile_picture.name
                    delete_res = supabase.storage.from_("user-uploads").remove([previous_file_path])
                    #print(f"Previous profile picture deletion result: {delete_res}")
                except Exception as delete_error:
                    print(f"Warning: Could not delete previous profile picture: {delete_error}")
                    # Continue with upload even if deletion fails

            file_bytes = file_obj.read()

            # Upload to Supabase Storage
            res = supabase.storage.from_("user-uploads").upload(
                storage_key,
                file_bytes,
                {"content-type": file_obj.content_type}
            )
            if isinstance(res, dict) and res.get("error"):
                return Response({"error": res["error"]["message"]}, status=status.HTTP_400_BAD_REQUEST)

            # Set profile_picture field to the storage key or URL
            user.profile_picture = storage_key  # or construct a full URL if needed
            user.save(update_fields=['profile_picture'])

            # No local file to delete since file is read directly from upload

            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # return Response(data, status=status.HTTP_200_OK)


        # except Exception as e:
        #     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user




class UserProfilePictureGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = supabase.auth.api.get_user(user.id)
        profile_picture_key = None
        if user_data and user_data.user_metadata:
            profile_picture_key = user_data.user_metadata.get('profile_picture')
        if profile_picture_key:
            url = supabase.storage.from_('user-uploads').get_public_url(profile_picture_key).get('publicURL')
            return Response({'profile_picture_url': url}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Profile picture not found'}, status=status.HTTP_404_NOT_FOUND)


class UserProfilePictureGetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile_picture_key = user.profile_picture
        if not profile_picture_key:
            return Response({"error": "User has no profile picture."}, status=status.HTTP_404_NOT_FOUND)

        supabase_url = settings.SUPABASE_URL
        bucket_name = "user-uploads"

        # Construct public URL (assuming bucket is public or using signed URLs would require more implementation)
        image_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{profile_picture_key}"

        return Response({"profile_picture_url": image_url}, status=status.HTTP_200_OK)




class UserFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

        folder_name = f"user_{request.user.id}"

        try:
            files = supabase.storage.from_("user-uploads").list(
                path=folder_name,
                options={"limit": 100, "offset": 0, "sortBy": {"column": "name", "order": "asc"}},
            )

            # helper to build path once
            def full_path(name: str) -> str:
                return f"{folder_name}/{name}"

            # ----- OPTION A: bucket is PUBLIC -----
            # get_public_url = supabase.storage.from_("user-uploads").get_public_url

            # ----- OPTION B: bucket is PRIVATE (recommended) -----
            create_signed_url = supabase.storage.from_("user-uploads").create_signed_url
            EXPIRES_IN = 3600  # seconds

            files_info = []
            for f in files:
                if not f["name"].lower().endswith(".pdf"):
                    continue

                path = full_path(f["name"])

                # PUBLIC:
                # url = get_public_url(path)

                # PRIVATE (signed):
                signed = create_signed_url(path, EXPIRES_IN)
                url = signed.get("signedURL") or signed.get("signed_url")  # lib versions differ

                files_info.append({
                    "name": f["name"],
                    "updated_at": f.get("updated_at"),
                    "created_at": f.get("created_at"),
                    "id": f.get("id"),
                    "url": url,
                })

            return Response({"files": files_info}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = f"{user.id}/{file_obj.name}"

        try:
            response = supabase.storage.from_('files').upload(file_name, file_obj)
            if response:
                file_instance = File.objects.create(
                    name=file_obj.name,
                    user=user,
                    supabase_path=file_name
                )
                file_instance.save()
                return Response({'message': 'File uploaded successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'File upload failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        folder = f"user_{user.id}"

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        ext = uploaded_file.name.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        storage_key = f"{folder}/{filename}"

        try:
            file_bytes = uploaded_file.read()

            # 1) Upload to Supabase
            res = supabase.storage.from_("user-uploads").upload(
                storage_key,
                file_bytes,
                {"content-type": uploaded_file.content_type}
            )
            if isinstance(res, dict) and res.get("error"):
                return Response({"error": res["error"]["message"]}, status=status.HTTP_400_BAD_REQUEST)

            # 2) Save DB row without embedding pipeline
            with transaction.atomic():
                file_obj = File.objects.create(
                    user=user,
                    file=uploaded_file,          # FileField writes to MEDIA_ROOT/uploads/...
                    filename=uploaded_file.name, # original name
                    storage_key=storage_key
                )

            return Response(
                {
                    "message": "File uploaded successfully",
                    "file_id": file_obj.id,
                    "storage_key": storage_key
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Optional: clean up supabase object if DB/embedding failed
            try:
                supabase.storage.from_("user-uploads").remove([storage_key])
            except Exception:
                pass

            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class UserFileDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    # def delete(self, request, file_id):
    #     user = request.user
    #     supabase_token = request.headers.get("Authorization", "").replace("Bearer ", "")

    #     try:
    #         # Initialize supabase client with service role key
    #         supabase = create_client(
    #             settings.SUPABASE_URL,
    #             settings.SUPABASE_SERVICE_ROLE_KEY,
    #             options={
    #                 "auto_refresh_token": True,
    #                 "persist_session": True,
    #                 "detect_session_in_url": True,
    #                 "storage": None,
    #             },
    #         )

    #         # Validate file ownership by id
    #         file_obj = File.objects.filter(id=file_id, user=user).first()
    #         if not file_obj:
    #             return Response({"error": "File not found or you do not have permission."}, status=status.HTTP_404_NOT_FOUND)

    #         file_path = file_obj.storage_key

    #         # Remove file from Supabase storage
    #         removed = supabase.storage.from_("user-uploads").remove([file_path])
    #         if isinstance(removed, dict) and removed.get("error"):
    #             return Response({"error": removed["error"]["message"]}, status=status.HTTP_400_BAD_REQUEST)

    #         # Remove corresponding embeddings from ChromaDB
    #         try:
    #             collection = chroma_client.get_collection(name="user_files")  # Change to your collection name
    #             collection.delete(where={"file_id": str(file_id)})
    #         except Exception:
    #             pass  # Log error if needed

    #         # Remove DB record for the file
    #         file_obj.delete()

    #         return Response({"message": "File deleted."}, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # permission_classes = [IsAuthenticated]

    def delete(self, request, file_name: str, *args, **kwargs):
        # Server-side key (or a valid Supabase user JWT in another header if you insist)
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

        user = request.user
        folder = f"user_{user.id}"
        file_path = f"{folder}/{file_name}"

        # (Optional) simple path traversal guard
        if "/" in file_name or ".." in file_name:
            return Response({"error": "Invalid file name."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # (Optional) verify ownership before delete
            # Cheap check using list; for large folders use your DB instead
            files = supabase.storage.from_("user-uploads").list(folder)
            if not any(f["name"] == file_name for f in files):
                return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

            # Remove from storage
            removed = supabase.storage.from_("user-uploads").remove([file_path])
            # v2: returns list of dicts; v1: dict with data/error
            if isinstance(removed, dict) and removed.get("error"):
                return Response({"error": removed["error"]["message"]}, status=status.HTTP_400_BAD_REQUEST)

            # Remove from DB (wrap to keep consistency)
            with transaction.atomic():
                from .models import File
                file_obj = File.objects.filter(user=user, storage_key=file_path).first()
                if file_obj:
        
                    # Delete local file
                    file_obj.file.delete(save=False)
                    file_obj.delete()

            return Response({"message": "File deleted."}, status=status.HTTP_200_OK)
        except Exception as e:
            # log.exception("Supabase delete failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 


#for below code, i think there is no use of it 


# class FileListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user = request.user
#         files = File.objects.filter(user=user)
#         serializer = FileSerializer(files, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

# class FileDeleteView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, pk):
#         user = request.user
#         try:
#             file_instance = File.objects.get(pk=pk, user=user)
#         except File.DoesNotExist:
#             return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

#         try:
#             supabase.storage.from_('files').remove([file_instance.supabase_path])
#             file_instance.delete()
#             return Response({'message': 'File deleted successfully'}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)})
#             'first_name','last_name',
#             'phone_number','gender','date_of_birth'
        
#         missing = [f for f in required if not data.get(f)]
#         if missing:
#             return Response(
#                 {'error': f"Missing fields: {', '.join(missing)}"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         supabase = create_client(
#             settings.SUPABASE_URL,
#             settings.SUPABASE_SERVICE_ROLE_KEY
#         )


#         try:
#             resp = supabase.auth.sign_up({
#                 'email':    data['email'],
#                 'password': data['password'],
#                 'options': {
#                     'redirect_to': settings.BASE_URL_SIGNIN
#                 }
#             })
#         except AuthApiError as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#         # At this point, resp.user is guaranteed to exist
#         supa_user = resp.user  # <— has .id and .email :contentReference[oaicite:0]{index=0}

#         # Push metadata into Supabase
#         metadata = {
#             'first_name':   data['first_name'],
#             'last_name':    data['last_name'],
#             'phone_number': data['phone_number'],
#             'gender':       data['gender'],
#             'date_of_birth': data['date_of_birth']
#         }
#         try:
#             supabase.auth.admin.update_user_by_id(
#                 supa_user.id,
#                 {'user_metadata': metadata}
#             )
#         except AuthApiError as e:
#             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Mirror into Django
#         try:
#             dob = datetime.strptime(data['date_of_birth'], "%Y-%m-%d").date()
#         except ValueError:
#             dob = None

#         User.objects.create_user(
#             id=supa_user.id,
#             email=supa_user.email,
#             first_name=metadata['first_name'],
#             last_name=metadata['last_name'],
#             phone_number=metadata['phone_number'],
#             gender=metadata['gender'],
#             date_of_birth=dob
#         )

#         return Response(
#             {'message': 'Registration successful. Please verify your email.'},
#             status=status.HTTP_201_CREATED
#         )


# class SupabaseOptions:
#     def __init__(self, token):
#         self.headers = {"Authorization": f"Bearer {token}"}
#         self.auto_refresh_token = False
#         self.persist_session = False
#         self.detect_session_in_url = False
#         self.storage = None
#         self.flow_type = None
#         self.httpx_client = None

# class FileDeleteView(DestroyAPIView):
#     permission_classes = [IsAuthenticated]
#     queryset = File.objects.all()
#     serializer_class = FileSerializer

#     def perform_destroy(self, instance):
#         # Delete file from Supabase Storage
#         try:
#             if getattr(instance, 'storage_key', None):
#                 supabase.storage.from_('user-uploads').remove([instance.storage_key])
#         except Exception as e:
#             pass  # Log error if needed
#         # Delete from local storage and database
#         instance.file.delete(save=False)
#         instance.delete()


# class FileListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         user_id = self.request.user.id
#         files = File.objects.filter(user_id=user_id)
#         serializer = FileSerializer(files, many=True)
#         return Response(serializer.data)

# class FileDeleteView(APIView):
#     permission_classes = [IsAuthenticated]

#     def delete(self, request, pk):
#         user_id = self.request.user.id
#         try:
#             file_obj = File.objects.get(pk=pk, user_id=user_id)
#         except File.DoesNotExist:
#             return Response({'error': 'File not found.'}, status=404)
#         # Remove from ChromaDB using LangChain Chroma vector store
#         if file_obj.chroma_collection:
#             from langchain_community.vectorstores import Chroma
#             user_chroma_dir = get_user_chroma_dir(user_id)
#             vs = Chroma(
#                 collection_name=file_obj.chroma_collection,
#                 embedding_function=text_emb,
#                 persist_directory=user_chroma_dir,
#             )
#             vs.delete(where={"file_id": file_obj.id})
#             vs.persist()
#             vs.persist()  # Add this line to persist deletion
#         # Delete file from storage and DB
#         file_obj.file.delete(save=False)
#         file_obj.delete()
#         return Response({'message': 'File deleted.'}, status=204)

# class ChatListCreateView(generics.ListCreateAPIView):
#     serializer_class = ChatSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user  # this is a Django User instance now
#         user_id = user.id
#         return Chat.objects.filter(user_id=user_id)

#     def perform_create(self, serializer):
#         user = self.request.user  # this is a Django User instance now
#         user_id = user.id
#         serializer.save(user_id=user_id)


# def serialize_message(m: Message):
#     return {
#         "id": m.id,
#         "chat_id": str(m.chat_id),
#         "sender_id": str(m.sender_id) if m.sender_id else None,
#         "sender_type": m.sender_type,
#         "content": m.content,
#         "timestamp": m.timestamp.isoformat(),
#     }
    
# class MessageListCreateView(generics.ListCreateAPIView):
#     serializer_class = MessageSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         chat_id = self.kwargs["chat_id"]
#         return (Message.objects
#                 .filter(chat_id=chat_id, chat__user_id=self.request.user.id)
#                 .order_by("timestamp"))

#     def list(self, request, *args, **kwargs):
#         msgs = self.get_queryset()
#         data = [{
#             "id": m.id,
#             "chat_id": str(m.chat_id),
#             "user_message": m.content if m.sender_type == "user" else None,
#             "ai_response":  m.content if m.sender_type == "ai"   else None,
#             "rag_sources":  m.sources  if m.sender_type == "ai"   else None,
#         } for m in msgs]
#         return Response({"messages": data}, status=status.HTTP_200_OK)

#     def create(self, request, *args, **kwargs):
#         user    = request.user
#         chat_id = self.kwargs["chat_id"]
#         chat    = get_object_or_404(Chat, id=chat_id, user_id=user.id)

#         # 1) Save user message
#         ser = self.get_serializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         user_msg = ser.save(sender=user, sender_type="user", chat=chat)

#         # 2) RAG -> AI message
#         rag = run_rag_pipeline(user, user_msg.content)
#         ai_msg = Message.objects.create(
#             chat=chat,
#             sender=None,
#             sender_type="ai",
#             content=rag["answer"],
#             sources=rag.get("sources", [])
#         )

#         # 3) Flat response
#         return Response(
#             {
#                 "id": ai_msg.id,                     # or user_msg.id / chat_id — your choice
#                 "chat_id": str(chat.id),
#                 "user_message": user_msg.content,
#                 "ai_response":  ai_msg.content,
#                 "rag_sources": rag.get("sources", [])  # optional
#             },
#             status=status.HTTP_201_CREATED
#         )




#     def post(self, request):
#         refresh_token = request.data.get("refresh_token")
#         if not refresh_token:
#             return Response({"error": "refresh_token is required"}, status=status.HTTP_400_BAD_REQUEST)

#         supabase_url = settings.SUPABASE_URL
#         supabase_key = settings.SUPABASE_KEY
#         supabase = create_client(supabase_url, supabase_key)

#         try:
#             data = supabase.auth.refresh_session(refresh_token)
#             if data.session and data.session.access_token and data.session.refresh_token:
#                 return Response({
#                     "access_token": data.session.access_token,
#                     "refresh_token": data.session.refresh_token
#                 })
#             else:
#                 return Response({"error": "Failed to refresh token"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)