from supabase import create_client, Client
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

_admin_client: Client | None = None

def get_admin_client() -> Client:
    """
    Returns a singleton Supabase admin client using the secret key.
    Use ONLY for server-side admin operations (Auth admin, Storage).
    Never use this client for user-facing data queries — use Django ORM instead.
    """
    global _admin_client
    if _admin_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SECRET_KEY:
            logger.error("Supabase credentials missing. Ensure SUPABASE_URL and SUPABASE_SECRET_KEY are set.")
            raise ValueError("Supabase credentials missing")
            
        _admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SECRET_KEY,  # sb_secret_... key
        )
    return _admin_client
