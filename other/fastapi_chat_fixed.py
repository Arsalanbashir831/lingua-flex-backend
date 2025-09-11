"""
Updated FastAPI chat with correct database connection to fetch user names
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from supabase import create_client, Client
import os
import jwt
from pydantic import BaseModel
import json

# Try to import Django settings to get database config
try:
    from rag_app.settings import DATABASES, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
    DB_CONFIG = DATABASES['default']
except ImportError:
    # Fallback configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'your-supabase-url')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'your-key')
    DB_CONFIG = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres', 
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }

# Try to import psycopg2, provide fallback if not available
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("Warning: psycopg2 not available. Install with: pip install psycopg2-binary")

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

def get_db_connection():
    """Get connection to Django database"""
    if not PSYCOPG2_AVAILABLE:
        print("psycopg2 not available - cannot connect to database")
        return None
        
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG.get('HOST', 'localhost'),
            database=DB_CONFIG.get('NAME', 'postgres'),
            user=DB_CONFIG.get('USER', 'postgres'),
            password=DB_CONFIG.get('PASSWORD', 'password'),
            port=DB_CONFIG.get('PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_user_details(user_id: str):
    """Fetch user details from Django database"""
    if not PSYCOPG2_AVAILABLE:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": "psycopg2 not installed - cannot fetch user details from database"
        }
    
    conn = get_db_connection()
    if not conn:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": "Database connection failed"
        }
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Fetch user data from core_user table
            cursor.execute("""
                SELECT id, email, first_name, last_name, role, phone_number, profile_picture
                FROM core_user 
                WHERE id = %s
            """, (user_id,))
            
            user_data = cursor.fetchone()
            
            if user_data:
                return {
                    "id": user_data["id"],
                    "email": user_data["email"],
                    "first_name": user_data["first_name"] or "",
                    "last_name": user_data["last_name"] or "",
                    "role": user_data["role"] or "UNKNOWN",
                    "phone_number": user_data["phone_number"],
                    "profile_picture": user_data["profile_picture"]
                }
            else:
                return {
                    "id": user_id,
                    "email": None,
                    "first_name": "",
                    "last_name": "",
                    "role": "UNKNOWN",
                    "error": "User not found in database"
                }
                
    except Exception as e:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": f"Database query failed: {str(e)}"
        }
    finally:
        conn.close()

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
        chat = existing.data[0]
    else:
        chat = supabase.table("chats").insert({
            "participant1": student_id,
            "participant2": teacher_id
        }).execute().data[0]
    
    # Fetch user details from Django database
    student_details = get_user_details(student_id)
    teacher_details = get_user_details(teacher_id)
    
    # Return enhanced response with student and teacher details
    return {
        "id": chat["id"],
        "student_id": student_id,
        "teacher_id": teacher_id,
        "student_details": student_details,
        "teacher_details": teacher_details,
        "created_at": chat["created_at"],
        # Keep original fields for backwards compatibility
        "participant1": chat["participant1"],
        "participant2": chat["participant2"]
    }

@app.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    messages = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return messages.data

# Test endpoint to check database connection
@app.get("/test-db")
def test_database_connection():
    """Test endpoint to verify database connection and user fetching"""
    if not PSYCOPG2_AVAILABLE:
        return {
            "status": "error",
            "message": "psycopg2 not installed",
            "solution": "Run: pip install psycopg2-binary"
        }
    
    conn = get_db_connection()
    if not conn:
        return {
            "status": "error", 
            "message": "Cannot connect to database",
            "config": {
                "host": DB_CONFIG.get('HOST'),
                "database": DB_CONFIG.get('NAME'),
                "user": DB_CONFIG.get('USER'),
                "port": DB_CONFIG.get('PORT')
            }
        }
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Test query to count users
            cursor.execute("SELECT COUNT(*) as user_count FROM core_user")
            result = cursor.fetchone()
            
            # Get a sample user
            cursor.execute("SELECT id, email, first_name, last_name, role FROM core_user LIMIT 1")
            sample_user = cursor.fetchone()
            
            return {
                "status": "success",
                "message": "Database connection working",
                "user_count": result["user_count"],
                "sample_user": dict(sample_user) if sample_user else None,
                "psycopg2_available": PSYCOPG2_AVAILABLE
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database query failed: {str(e)}"
        }
    finally:
        conn.close()

# Add more endpoints as needed for user listing, teacher listing, etc.
