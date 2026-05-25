import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel
from django.conf import settings

from core.supabase_client import get_admin_client
from chat.connections import active_connections
from chat.dependencies import get_current_user
from chat.services.email import send_teacher_notification_email
from chat.services.users import get_user_details

router = APIRouter()

@router.get("/chats/{user_id}")
def list_chats(user_id: str):
    # Return all chats for a user
    chats = (
        get_admin_client()
        .table("chats")
        .select("*")
        .or_(f"participant1.eq.{user_id},participant2.eq.{user_id}")
        .execute()
    )
    return chats.data


class ChatCreateRequest(BaseModel):
    student_id: str
    teacher_id: str


@router.post("/chats/start/")
def start_chat(payload: ChatCreateRequest):
    student_id = payload.student_id
    teacher_id = payload.teacher_id

    if str(student_id) == str(teacher_id):
        raise HTTPException(
            status_code=400, detail="You cannot initiate a chat with yourself"
        )

    # Ensure only one chat per pair (regardless of order)
    existing = (
        get_admin_client()
        .table("chats")
        .select("*")
        .or_(
            f"and(participant1.eq.{student_id},participant2.eq.{teacher_id}),and(participant1.eq.{teacher_id},participant2.eq.{student_id})"
        )
        .execute()
    )

    if existing.data:
        print(
            f"Existing chat found between student {student_id} and teacher {teacher_id}"
        )
        return existing.data[0]

    # Create new chat
    chat = (
        get_admin_client()
        .table("chats")
        .insert(
            {
                "id": str(uuid.uuid4()),
                "participant1": student_id,
                "participant2": teacher_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .execute()
    )

    print(f"New chat created between student {student_id} and teacher {teacher_id}")

    # Get the created chat data
    created_chat = chat.data[0]
    chat_id = created_chat.get("id")

    # Send email notification to teacher about new chat
    try:
        student_details = get_user_details(student_id)
        teacher_details = get_user_details(teacher_id)

        if student_details and teacher_details and chat_id:
            email_sent = send_teacher_notification_email(
                student_details, teacher_details, chat_id
            )

            if email_sent:
                print(
                    f"Email notification sent to teacher {teacher_details.get('email')} with chat ID {chat_id}"
                )
            else:
                print(
                    f"Failed to send email notification to teacher {teacher_details.get('email')}"
                )
        else:
            print(
                f"Could not fetch required data - Student: {'✓' if student_details else '✗'}, Teacher: {'✓' if teacher_details else '✗'}, Chat ID: {'✓' if chat_id else '✗'}"
            )

    except Exception as e:
        print(f"Error sending teacher notification: {str(e)}...")
        # Don't fail the chat creation if email fails

    return created_chat


@router.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    token: Optional[str] = Query(None),
):
    """
    WebSocket for real-time delivery of messages to connected clients.
    Messages are now SENT via POST /send-message/{chat_id} (HTTP), not through
    the socket — this keeps binary file uploads off the WebSocket stream.

    The socket still handles text-only quick messages for backward compatibility.
    """
    await websocket.accept()

    if not token:
        await websocket.send_json({"type": "error", "content": "Missing authentication token"})
        await websocket.close(code=1008)
        return

    try:
        user = await get_current_user(token)
        user_id = user["sub"]
    except Exception as e:
        await websocket.send_json({"type": "error", "content": f"Invalid or expired token: {str(e)}"})
        await websocket.close(code=1008)
        return

    key = f"{chat_id}:{user_id}"
    active_connections[key] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            message_content = data.get("content", "").strip()

            if not message_content:
                # Empty text with no file — ignore silently
                continue

            msg_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()

            # Persist text-only message
            get_admin_client().table("messages").insert(
                {
                    "id": msg_id,
                    "chat_id": chat_id,
                    "sender_id": user_id,
                    "content": message_content,
                    "timestamp": timestamp,
                }
            ).execute()

            # Broadcast to other participant(s) in the chat
            outgoing = {
                "id": msg_id,
                "sender_id": user_id,
                "content": message_content,
                "attachments": [],
                "timestamp": timestamp,
            }
            for k, ws in active_connections.items():
                if k.startswith(f"{chat_id}:") and k != key:
                    await ws.send_json(outgoing)

    except WebSocketDisconnect:
        active_connections.pop(key, None)
