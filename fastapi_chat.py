from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from supabase import create_client, Client
import os
import jwt
from pydantic import BaseModel
#from rag_app.settings import settings
from rag_app.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# SUPABASE_URL = SUPABASE_URL
# SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: Dict[str, WebSocket] = {}

async def get_current_user(token: str) -> dict:
    # Supabase JWT verification (client sends token in query params)
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload  # contains 'sub', 'email', 'role', etc.
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, token: str):
    user = await get_current_user(token)
    user_id = user["sub"]
    await websocket.accept()
    key = f"{chat_id}:{user_id}"
    active_connections[key] = websocket
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("content")
            # Save message to Supabase
            supabase.table("messages").insert({
                "chat_id": chat_id,
                "sender_id": user_id,
                "content": message
            }).execute()
            # Broadcast to other participant
            for k, ws in active_connections.items():
                if k.startswith(f"{chat_id}:") and k != key:
                    await ws.send_json({
                        "sender_id": user_id,
                        "content": message
                    })
    except WebSocketDisconnect:
        del active_connections[key]

@app.get("/chats/{user_id}")
def list_chats(user_id: str):
    # Return all chats for a user
    chats = supabase.table("chats").select("*").or_(f"participant1.eq.{user_id},participant2.eq.{user_id}").execute()
    return chats.data

class ChatCreateRequest(BaseModel):
    student_id: str
    teacher_id: str

@app.post("/chats/start/")
def start_chat(payload: ChatCreateRequest):
    student_id = payload.student_id
    teacher_id = payload.teacher_id
    # Ensure only one chat per pair (regardless of order)
    existing = supabase.table("chats").select("*").or_(
        f"and(participant1.eq.{student_id},participant2.eq.{teacher_id}),and(participant1.eq.{teacher_id},participant2.eq.{student_id})"
    ).execute()
    if existing.data:
        return existing.data[0]
    chat = supabase.table("chats").insert({
        "participant1": student_id,
        "participant2": teacher_id
    }).execute()
    return chat.data[0]

@app.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    messages = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return messages.data

# Add more endpoints as needed for user listing, teacher listing, etc.
