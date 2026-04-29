import uuid
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from supabase import create_client

def get_supabase_client():
    """Initialize Supabase client from settings"""
    url = getattr(settings, "SUPABASE_URL", "")
    key = getattr(settings, "SUPABASE_ANON_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)

def handle_blog_thumbnail_upload(thumbnail_file, teacher_id):
    """
    Handle validation and upload of blog thumbnail to Supabase.
    Returns: (public_url, error_response)
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if thumbnail_file.content_type not in allowed_types:
        return None, Response(
            {"error": "Invalid thumbnail file type. Only JPEG, PNG, WebP, and GIF images are allowed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if thumbnail_file.size > max_size:
        return None, Response(
            {"error": "Thumbnail file too large. Maximum size is 5MB"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        supabase = get_supabase_client()
        if not supabase:
            return None, Response(
                {"error": "Supabase configuration missing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Create unique filename
        file_extension = thumbnail_file.name.split(".")[-1].lower()
        unique_filename = f"blog_thumbnails/{teacher_id}/{uuid.uuid4()}.{file_extension}"
        
        # Get bucket name from settings or default
        bucket_name = getattr(settings, "SUPABASE_BLOG_IMAGE_BUCKET", "blog-images")

        # Upload to Supabase
        supabase.storage.from_(bucket_name).upload(
            unique_filename,
            thumbnail_file.read(),
            {
                "content-type": thumbnail_file.content_type,
                "cache-control": "3600",
                "upsert": "false",
            },
        )

        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        return public_url, None

    except Exception as e:
        return None, Response(
            {"error": f"Failed to upload thumbnail: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
