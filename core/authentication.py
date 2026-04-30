# core/authentication.py
import jwt
from jwt import PyJWKClient
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions

import logging

logger = logging.getLogger(__name__)

# Initialize the JWK Client once to benefit from internal caching of public keys.
# This prevents a network request on every single API call.
_jwks_client = None

def get_jwks_client():
    global _jwks_client
    if _jwks_client is None:
        # JWKS endpoint is standard for Supabase projects
        jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client

class SupabaseTokenAuthentication(BaseAuthentication):
    """
    Authenticates requests by locally verifying the Supabase JWT signature
    using JWKS (JSON Web Key Set).
    
    This is the "Future-Proof" approach that works with Supabase's new 
    Asymmetric keys (ECC P-256) and handles key rotation automatically.
    """

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:].strip()
        if not token:
            return None

        try:
            # 1. Get the public signing key from Supabase (cached)
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # 2. Decode and verify locally
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "HS256"],
                # Supabase uses 'authenticated' audience for login tokens
                options={"verify_aud": False}, 
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("Token has expired.")
        except Exception as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise exceptions.AuthenticationFailed(f"Invalid token: {str(e)}")

        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("Token payload missing user ID (sub).")

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found.")

        return (user, None)

    @staticmethod
    def verify_token_payload(token):
        """
        Helper method to verify a token and return its payload.
        Useful for one-off verifications (like password reset).
        """
        try:
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "HS256"],
                options={"verify_aud": False},
            )
        except Exception as e:
            logger.error(f"Manual token verification failed: {str(e)}")
            return None
