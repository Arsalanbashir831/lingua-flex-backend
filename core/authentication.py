# core/authentication.py
import requests
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth import authenticate as dj_authenticate

class SupabaseBackend(BaseBackend):
    def authenticate(self, request, token=None):
        if not token:
            return None

        project_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
        api_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "") or getattr(settings, "SUPABASE_ANON_KEY", "")
        if not project_url or not api_key:
            return None  # or raise

        url = f"{project_url}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": api_key,
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return None

        data = resp.json()
        user_id = data.get("id")
        email = data.get("email")
        if not user_id or not email:
            return None

        User = get_user_model()
        
        try:
            # Try to get user by ID first (OAuth users)
            user = User.objects.get(id=user_id)
            return user
        except User.DoesNotExist:
            try:
                # Try to get user by email (in case of ID mismatch)
                user = User.objects.get(email=email)
                return user
            except User.DoesNotExist:
                # Create new user only if neither ID nor email exists
                try:
                    user = User.objects.create(
                        id=user_id, 
                        email=email, 
                        username=email.split('@')[0]
                    )
                    return user
                except Exception as e:
                    # If creation fails, try one more time to get by email
                    # (handles race conditions)
                    try:
                        return User.objects.get(email=email)
                    except User.DoesNotExist:
                        return None

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SupabaseTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith(self.keyword):
            return None

        token = auth_header[len(self.keyword):].strip()
        user = dj_authenticate(request=request, token=token)
        if user is None:
            raise exceptions.AuthenticationFailed("Invalid or expired Supabase token")
        return (user, None)
