"""
Simplified FastAPI chat with step-by-step database connection debugging
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from supabase import create_client, Client
import os
import jwt
from pydantic import BaseModel
import json

# Try to import Django settings
try:
    from rag_app.settings import DATABASES, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
    DJANGO_SETTINGS_AVAILABLE = True
    DB_CONFIG = DATABASES.get('default', {})
    print("✅ Django settings loaded successfully")
    print(f"Database config: {DB_CONFIG.get('ENGINE')} - {DB_CONFIG.get('NAME')}")
except ImportError as e:
    print(f"⚠️  Could not import Django settings: {e}")
    DJANGO_SETTINGS_AVAILABLE = False
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

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
    print("✅ psycopg2 is available")
except ImportError as e:
    PSYCOPG2_AVAILABLE = False
    print(f"❌ psycopg2 not available: {e}")
    print("Install with: pip install psycopg2-binary")

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

def test_database_connection_steps():
    """Test database connection step by step"""
    
    result = {
        "django_settings": DJANGO_SETTINGS_AVAILABLE,
        "psycopg2_available": PSYCOPG2_AVAILABLE,
        "connection_test": None,
        "user_query_test": None,
        "config": DB_CONFIG
    }
    
    if not PSYCOPG2_AVAILABLE:
        result["connection_test"] = "FAILED - psycopg2 not installed"
        return result
    
    # Test basic connection
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG.get('HOST', 'localhost'),
            database=DB_CONFIG.get('NAME', 'postgres'),
            user=DB_CONFIG.get('USER', 'postgres'),
            password=DB_CONFIG.get('PASSWORD', 'password'),
            port=DB_CONFIG.get('PORT', '5432')
        )
        result["connection_test"] = "SUCCESS"
        
        # Test user table query
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM core_user")
                count_result = cursor.fetchone()
                result["user_query_test"] = f"SUCCESS - Found {count_result['count']} users"
                
                # Get sample user
                cursor.execute("SELECT id, email, first_name, last_name, role FROM core_user LIMIT 1")
                sample = cursor.fetchone()
                if sample:
                    result["sample_user"] = dict(sample)
                    
        except Exception as e:
            result["user_query_test"] = f"FAILED - {str(e)}"
            
        conn.close()
        
    except Exception as e:
        result["connection_test"] = f"FAILED - {str(e)}"
    
    return result

def get_user_details_safe(user_id: str):
    """Safely fetch user details with detailed error reporting"""
    
    if not PSYCOPG2_AVAILABLE:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": "psycopg2 not installed - run: pip install psycopg2-binary"
        }
    
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG.get('HOST', 'localhost'),
            database=DB_CONFIG.get('NAME', 'postgres'),
            user=DB_CONFIG.get('USER', 'postgres'),
            password=DB_CONFIG.get('PASSWORD', 'password'),
            port=DB_CONFIG.get('PORT', '5432')
        )
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
                    "error": f"User {user_id} not found in core_user table"
                }
                
        conn.close()
                
    except psycopg2.OperationalError as e:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": f"Database connection failed: {str(e)}"
        }
    except Exception as e:
        return {
            "id": user_id,
            "email": None,
            "first_name": "",
            "last_name": "",
            "role": "UNKNOWN",
            "error": f"Database error: {str(e)}"
        }

# Basic endpoints
async def get_current_user(token: str) -> dict:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
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
            supabase.table("messages").insert({
                "chat_id": chat_id,
                "sender_id": user_id,
                "content": message
            }).execute()
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
    
    # Fetch user details with safe error handling
    student_details = get_user_details_safe(student_id)
    teacher_details = get_user_details_safe(teacher_id)
    
    return {
        "id": chat["id"],
        "student_id": student_id,
        "teacher_id": teacher_id,
        "student_details": student_details,
        "teacher_details": teacher_details,
        "created_at": chat["created_at"],
        "participant1": chat["participant1"],
        "participant2": chat["participant2"]
    }

@app.get("/messages/{chat_id}")
def get_messages(chat_id: str):
    messages = supabase.table("messages").select("*").eq("chat_id", chat_id).order("timestamp").execute()
    return messages.data

# Diagnostic endpoints
@app.get("/test-db")
def test_database():
    """Comprehensive database connection test"""
    return test_database_connection_steps()

@app.get("/test-user/{user_id}")
def test_user_fetch(user_id: str):
    """Test fetching a specific user"""
    return get_user_details_safe(user_id)

@app.get("/debug-config")
def debug_configuration():
    """Show current configuration for debugging"""
    return {
        "django_settings_available": DJANGO_SETTINGS_AVAILABLE,
        "psycopg2_available": PSYCOPG2_AVAILABLE,
        "database_config": {
            "engine": DB_CONFIG.get('ENGINE'),
            "name": DB_CONFIG.get('NAME'),
            "user": DB_CONFIG.get('USER'),
            "host": DB_CONFIG.get('HOST'),
            "port": DB_CONFIG.get('PORT'),
            "password_set": bool(DB_CONFIG.get('PASSWORD'))
        },
        "supabase_url_set": bool(SUPABASE_URL and SUPABASE_URL != 'your-supabase-url'),
        "environment": "development"
    }

# Add more endpoints as needed for user listing, teacher listing, etc.
