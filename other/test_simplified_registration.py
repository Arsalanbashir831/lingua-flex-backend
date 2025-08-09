# test_simplified_registration.py
"""
Test script for the simplified registration system
This script demonstrates how to use the new simplified registration and profile update APIs
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/accounts"

def test_student_registration_and_update():
    """Test student registration and profile update flow"""
    
    print("=== Testing Student Registration and Profile Update ===\n")
    
    # 1. Register a new student
    print("1. Registering a new student...")
    student_data = {
        "email": "student@example.com",
        "password": "securepassword123",
        "full_name": "John Doe",
        "role": "student"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=student_data)
    print(f"Registration Response: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}\n")
    
    if response.status_code != 201:
        print("Registration failed, stopping test")
        return
    
    # Note: In real scenario, you would get the token from Supabase authentication
    # For this test, we'll simulate having a token
    # student_token = "your_supabase_jwt_token_here"
    
    print("2. Student would now authenticate with Supabase to get a token")
    print("3. Then use the token to update their profile:\n")
    
    # Simulate profile update request
    print("Profile Update Request (PUT /api/accounts/profile/update-student/):")
    profile_update = {
        "bio": "I'm passionate about learning new languages and cultures",
        "city": "New York",
        "country": "USA",
        "postal_code": "10001",
        "status": "Currently learning Spanish and French",
        "native_language": "English",
        "learning_language": "Spanish"
    }
    print(f"Headers: Authorization: Bearer <student_token>")
    print(f"Body: {json.dumps(profile_update, indent=2)}\n")

def test_teacher_registration_and_update():
    """Test teacher registration and profile update flow"""
    
    print("=== Testing Teacher Registration and Profile Update ===\n")
    
    # 1. Register a new teacher
    print("1. Registering a new teacher...")
    teacher_data = {
        "email": "teacher@example.com",
        "password": "securepassword123",
        "full_name": "Jane Smith",
        "role": "teacher"
    }
    
    response = requests.post(f"{BASE_URL}/register/", json=teacher_data)
    print(f"Registration Response: {response.status_code}")
    print(f"Response Body: {json.dumps(response.json(), indent=2)}\n")
    
    if response.status_code != 201:
        print("Registration failed, stopping test")
        return
    
    print("2. Teacher would now authenticate with Supabase to get a token")
    print("3. Then use the token to update their profile:\n")
    
    # Simulate teacher profile update request
    print("Teacher Profile Update Request (PUT /api/accounts/teacher/update/):")
    teacher_profile_update = {
        # Teacher-specific fields
        "qualification": "Master's in English Literature, TESOL Certified",
        "experience_years": 5,
        "certificates": ["TESOL", "IELTS Examiner", "Business English Certificate"],
        "about": "Experienced English teacher specializing in business communication and conversation practice",
        
        # User profile fields (can be updated together)
        "bio": "Professional English teacher with 5 years of international experience",
        "city": "London",
        "country": "UK",
        "postal_code": "SW1A 1AA",
        "status": "Available for new students - flexible schedule",
        "native_language": "English",
        "learning_language": ""
    }
    print(f"Headers: Authorization: Bearer <teacher_token>")
    print(f"Body: {json.dumps(teacher_profile_update, indent=2)}\n")

def show_api_endpoints():
    """Display all available API endpoints"""
    
    print("=== Available API Endpoints ===\n")
    
    endpoints = [
        {
            "method": "POST",
            "url": "/api/accounts/register/",
            "description": "Register new user (student or teacher)",
            "auth": "No"
        },
        {
            "method": "GET",
            "url": "/api/accounts/profile/me/",
            "description": "Get current user's profile",
            "auth": "Required"
        },
        {
            "method": "PUT/PATCH",
            "url": "/api/accounts/profile/update-student/",
            "description": "Update student profile",
            "auth": "Required (Student only)"
        },
        {
            "method": "GET",
            "url": "/api/accounts/teacher/me/",
            "description": "Get current teacher's profile",
            "auth": "Required (Teacher only)"
        },
        {
            "method": "PUT/PATCH",
            "url": "/api/accounts/teacher/update/",
            "description": "Update teacher profile",
            "auth": "Required (Teacher only)"
        },
        {
            "method": "GET",
            "url": "/api/accounts/teacher/list/",
            "description": "List all active teachers",
            "auth": "No"
        }
    ]
    
    for endpoint in endpoints:
        print(f"{endpoint['method']} {endpoint['url']}")
        print(f"  Description: {endpoint['description']}")
        print(f"  Authentication: {endpoint['auth']}\n")

def show_usage_instructions():
    """Show step-by-step usage instructions"""
    
    print("=== Usage Instructions ===\n")
    
    print("STEP 1: Start your Django server")
    print("  python manage.py runserver\n")
    
    print("STEP 2: Register a user")
    print("  POST /api/accounts/register/")
    print("  Required fields: email, password, full_name, role\n")
    
    print("STEP 3: User authenticates with Supabase")
    print("  (This happens in your frontend application)")
    print("  User receives JWT token from Supabase\n")
    
    print("STEP 4: Update profile based on role")
    print("  For Students:")
    print("    PUT/PATCH /api/accounts/profile/update-student/")
    print("    Include: bio, city, country, learning preferences, etc.\n")
    
    print("  For Teachers:")
    print("    PUT/PATCH /api/accounts/teacher/update/")
    print("    Include: qualifications, experience, certificates, etc.\n")
    
    print("STEP 5: Browse and interact")
    print("  Students can browse teachers: GET /api/accounts/teacher/list/")
    print("  Users can view their profiles: GET /api/accounts/profile/me/\n")

if __name__ == "__main__":
    print("LinguaFlex Simplified Registration System Test\n")
    print("=" * 50)
    
    try:
        show_usage_instructions()
        show_api_endpoints()
        test_student_registration_and_update()
        test_teacher_registration_and_update()
        
        print("=== Test Complete ===")
        print("Note: Actual profile updates require valid Supabase authentication tokens")
        print("This test only demonstrates the registration endpoint and shows example requests")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Django server.")
        print("Make sure your Django server is running on http://localhost:8000")
        print("Run: python manage.py runserver")
