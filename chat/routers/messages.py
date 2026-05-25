import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from django.conf import settings

from core.supabase_client import get_admin_client
from chat.connections import active_connections
from chat.dependencies import get_current_user, assert_participant
from chat.services.file_upload import validate_file, sanitize_filename

router = APIRouter()

@router.post("/send-message/{chat_id}")
async def send_message(
    chat_id: str,
    token: str,
    content: Optional[str] = Form(default=None),
    files: Optional[List[UploadFile]] = File(default=None),
):
    """
    Unified endpoint to send a chat message with optional file attachments.

    - content  : optional text body / caption
    - files    : optional list of files (multipart, field name "files")

    At least one of content or files must be provided.
    Max files per message: settings.CHAT_MAX_FILES_PER_MESSAGE (default 10).

    Flow:
      1. Auth + participant check
      2. Validate each file (magic-byte MIME detection, size limits)
      3. Upload valid files to Supabase Storage (atomic: rollback all on any failure)
      4. Persist Message row + MessageAttachment rows to DB
      5. Broadcast full payload to the other participant's active WebSocket
      6. Return the saved message payload
    """
    # 1. Auth
    user = await get_current_user(token)
    user_id = user["sub"]

    # 2. Participant guard
    assert_participant(chat_id, user_id)

    # 3. Basic content validation
    content_text = (content or "").strip() or None
    file_list = [f for f in (files or []) if f and f.filename]

    if content_text is None and not file_list:
        raise HTTPException(
            status_code=400,
            detail="A message must have text content, at least one file, or both.",
        )

    max_files = getattr(settings, "CHAT_MAX_FILES_PER_MESSAGE", 10)
    if len(file_list) > max_files:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_files} files per message. You sent {len(file_list)}.",
        )

    allowed_mimes = getattr(settings, "CHAT_ALLOWED_MIME_TYPES", [])
    max_size = getattr(settings, "CHAT_FILE_MAX_SIZE_BYTES", 10 * 1024 * 1024)
    video_mimes = getattr(settings, "CHAT_VIDEO_MIME_TYPES", [])
    video_max_size = getattr(settings, "CHAT_VIDEO_MAX_SIZE_BYTES", 50 * 1024 * 1024)
    bucket = getattr(settings, "CHAT_UPLOADS_BUCKET", "chat-uploads")

    # 4. Read + validate each file
    validated_files = []  # list of (file_bytes, original_name, detected_mime, safe_ext)
    for upload in file_list:
        file_bytes = await upload.read()
        safe_name = sanitize_filename(upload.filename or "file")
        detected_mime, safe_ext = validate_file(
            file_bytes, safe_name, allowed_mimes, max_size, video_mimes, video_max_size
        )
        validated_files.append((file_bytes, safe_name, detected_mime, safe_ext))

    # 5. Upload files to Supabase Storage (atomic rollback on any failure)
    uploaded_paths: list[str] = []
    attachment_meta: list[dict] = []

    for file_bytes, original_name, detected_mime, safe_ext in validated_files:
        storage_path = f"{chat_id}/{user_id}/{uuid.uuid4()}.{safe_ext}"
        try:
            get_admin_client().storage.from_(bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": detected_mime},
            )
            uploaded_paths.append(storage_path)
            public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
            attachment_meta.append(
                {
                    "file_url": public_url,
                    "file_name": original_name,
                    "file_type": detected_mime,
                    "file_size": len(file_bytes),
                }
            )
        except Exception as exc:
            # Rollback: delete every successfully uploaded file in this batch
            for path in uploaded_paths:
                try:
                    get_admin_client().storage.from_(bucket).remove([path])
                except Exception:
                    pass  # Best-effort cleanup
            raise HTTPException(
                status_code=502,
                detail=f"Failed to upload file '{original_name}' to storage: {str(exc)}",
            )

    # 6. Persist message to DB
    msg_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    get_admin_client().table("messages").insert(
        {
            "id": msg_id,
            "chat_id": chat_id,
            "sender_id": user_id,
            "content": content_text,
            "timestamp": timestamp,
        }
    ).execute()

    # 7. Persist attachments to DB
    if attachment_meta:
        attachment_rows = [
            {
                "id": str(uuid.uuid4()),
                "message_id": msg_id,
                "file_url": a["file_url"],
                "file_name": a["file_name"],
                "file_type": a["file_type"],
                "file_size": a["file_size"],
                "uploaded_at": timestamp,
            }
            for a in attachment_meta
        ]
        get_admin_client().table("message_attachments").insert(attachment_rows).execute()

    # 8. Build outgoing payload
    outgoing = {
        "id": msg_id,
        "sender_id": user_id,
        "content": content_text,
        "attachments": attachment_meta,
        "timestamp": timestamp,
    }

    # 9. Broadcast to other participant(s) connected via WebSocket
    for k, ws in active_connections.items():
        if k.startswith(f"{chat_id}:") and not k.endswith(f":{user_id}"):
            try:
                await ws.send_json(outgoing)
            except Exception:
                pass  # Don't fail if the recipient's socket is momentarily down

    return outgoing


@router.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    """
    Returns all messages for a chat, with their attachments nested inline.
    Each message object:
      {
        id, chat_id, sender_id, content, timestamp,
        attachments: [ { id, file_url, file_name, file_type, file_size, uploaded_at }, ... ]
      }
    """
    messages = (
        get_admin_client()
        .table("messages")
        .select("*, attachments:message_attachments(*)")
        .eq("chat_id", chat_id)
        .order("timestamp")
        .execute()
    )
    return messages.data
