from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from supabase import create_client, Client
import os
import jwt
import resend
from pydantic import BaseModel
#from rag_app.settings import settings
from rag_app.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, BASE_URL

# Configure Resend for email notifications
resend.api_key = "re_SnbT8oXw_E49CfdTG9hpXcUbrc3i8NJjQ"

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

def send_teacher_notification_email(student_details: dict, teacher_details: dict, chat_id: str):
    """Send email notification to teacher when a student starts a chat"""
    try:
        # Get student's profile picture URL if available
        profile_picture_html = ""
        if student_details.get('profile_picture'):
            profile_picture_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <img src="{student_details.get('profile_picture')}" 
                     alt="Student Profile" 
                     style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #3498db;">
            </div>
            """
        
        # Create HTML email content with only student name and profile picture
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c3e50;">New Chat Request from Student</h2>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                {profile_picture_html}
                <h3 style="color: #3498db; margin: 10px 0;">
                    {student_details.get('first_name', '')} {student_details.get('last_name', '')}
                </h3>
            </div>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 0; color: #27ae60;">
                    <strong>📱 A student has initiated a chat conversation with you!</strong>
                </p>
                <p style="margin: 10px 0 0 0; color: #555;">
                    Please click the button below to respond to the student's message.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{BASE_URL}/teacher/chat?chatId={chat_id}" 
                   style="background-color: #3498db; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Open Chat Conversation
                </a>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <a href="{BASE_URL}/teacher/dashboard" 
                   style="background-color: #2c3e50; color: white; padding: 10px 25px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Go to LinguaFlex Dashboard
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #888; font-size: 12px; text-align: center;">
                This is an automated notification from LinguaFlex. Please do not reply to this email.
            </p>
        </div>
        """
        
        params = {
            "from": "LinguaFlex <onboarding@lordevs.com>",
            "to": [teacher_details.get('email')],
            "subject": f"New Chat Request from {student_details.get('first_name', 'Student')} {student_details.get('last_name', '')}",
            "html": html_content
        }
        
        email_result = resend.Emails.send(params)
        print(f"Email sent successfully to teacher: {email_result}")
        return True
        
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")
        return False

def get_user_details(user_id: str) -> dict:
    """Fetch user details from Django database via Supabase"""
    try:
        # Get user from core_user table including profile_picture
        user_response = supabase.table("core_user").select(
            "id, email, first_name, last_name, phone_number, role, gender, date_of_birth, profile_picture, created_at"
        ).eq("id", user_id).execute()
        
        if not user_response.data:
            return {}
            
        user_data = user_response.data[0]
        
        # Construct full profile picture URL if exists
        if user_data.get('profile_picture'):
            # Assuming Supabase storage URL structure
            supabase_url = SUPABASE_URL
            bucket_name = "user-uploads"
            user_data['profile_picture'] = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{user_data['profile_picture']}"
        
        # Get user profile from accounts_userprofile table
        profile_response = supabase.table("accounts_userprofile").select(
            "bio, city, country, postal_code, status, native_language, learning_language"
        ).eq("user_id", user_id).execute()
        
        # Merge user and profile data
        if profile_response.data:
            user_data.update(profile_response.data[0])
            
        return user_data
        
    except Exception as e:
        print(f"Error fetching user details for {user_id}: {str(e)}")
        return {}

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
        print(f"Existing chat found between student {student_id} and teacher {teacher_id}")
        return existing.data[0]
    
    # Create new chat
    chat = supabase.table("chats").insert({
        "participant1": student_id,
        "participant2": teacher_id
    }).execute()
    
    print(f"New chat created between student {student_id} and teacher {teacher_id}")
    
    # Get the created chat data
    created_chat = chat.data[0]
    chat_id = created_chat.get('id')
    
    # Send email notification to teacher about new chat
    try:
        # Get student and teacher details
        student_details = get_user_details(student_id)
        teacher_details = get_user_details(teacher_id)
        
        if student_details and teacher_details and chat_id:
            # Send email notification to teacher with chat link
            email_sent = send_teacher_notification_email(student_details, teacher_details, chat_id)
            
            if email_sent:
                print(f"Email notification sent to teacher {teacher_details.get('email')} with chat ID {chat_id}")
            else:
                print(f"Failed to send email notification to teacher {teacher_details.get('email')}")
        else:
            print(f"Could not fetch required data - Student: {'✓' if student_details else '✗'}, Teacher: {'✓' if teacher_details else '✗'}, Chat ID: {'✓' if chat_id else '✗'}")
            
    except Exception as e:
        print(f"Error sending teacher notification: {str(e)}")
        # Don't fail the chat creation if email fails
    
    return created_chat

@app.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    messages = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return messages.data

# Add more endpoints as needed for user listing, teacher listing, etc.
