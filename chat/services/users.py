from django.conf import settings
from core.supabase_client import get_admin_client

def get_user_details(user_id: str) -> dict:
    """Fetch user details from database via Supabase client"""
    try:
        user_response = get_admin_client().table("core_user").select("*").eq("id", user_id).execute()
        if not user_response.data:
            return {}

        user = user_response.data[0]

        user_data = {
            "id": str(user.get("id")),
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "phone_number": user.get("phone_number"),
            "role": user.get("role"),
            "gender": user.get("gender"),
            "date_of_birth": str(user.get("date_of_birth")) if user.get("date_of_birth") else None,
            "created_at": str(user.get("created_at")),
        }

        if user.get("profile_picture"):
            bucket_name = getattr(
                settings, "SUPABASE_USER_UPLOADS_BUCKET", "user-uploads"
            )
            user_data["profile_picture"] = (
                f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{user.get('profile_picture')}"
            )

        profile_response = get_admin_client().table("accounts_userprofile").select("*").eq("user_id", user_id).execute()
        if profile_response.data:
            profile = profile_response.data[0]
            user_data.update(
                {
                    "bio": profile.get("bio"),
                    "city": profile.get("city"),
                    "country": profile.get("country"),
                    "postal_code": profile.get("postal_code"),
                    "status": profile.get("status"),
                    "native_language": profile.get("native_language"),
                    "learning_language": profile.get("learning_language"),
                }
            )

        return user_data

    except Exception as e:
        print(f"Error fetching user details for {user_id}: {str(e)}")
        return {}
