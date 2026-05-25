from fastapi import HTTPException
from core.supabase_client import get_admin_client
from core.authentication import SupabaseTokenAuthentication

async def get_current_user(token: str) -> dict:
    """Verify Supabase JWT locally using JWKS — zero network calls, cryptographically secure."""
    payload = SupabaseTokenAuthentication.verify_token_payload(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def assert_participant(chat_id: str, user_id: str):
    """
    Raises HTTP 403 if user_id is not a participant of chat_id.
    Uses the Supabase admin client (bypasses RLS) for the check.
    """
    result = (
        get_admin_client()
        .table("chats")
        .select("participant1, participant2")
        .eq("id", chat_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat = result.data[0]
    if str(user_id) not in (str(chat["participant1"]), str(chat["participant2"])):
        raise HTTPException(status_code=403, detail="You are not a participant of this chat")
