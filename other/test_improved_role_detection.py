#!/usr/bin/env python3
"""
Test script for improved role detection in Django chats endpoint
This script tests the enhanced role detection that checks both Supabase metadata and Django models
"""

import os
import sys
import django
import requests
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

def test_improved_chats_endpoint():
    """Test the improved chats endpoint with role detection"""
    
    # Test configuration
    BASE_URL = "http://127.0.0.1:8000"
    
    # Test with a valid token (replace with actual token)
    test_token = "your_test_token_here"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Improved Role Detection in Django Chats Endpoint")
    print("=" * 60)
    
    try:
        # Test the enhanced chats endpoint
        response = requests.get(
            f"{BASE_URL}/accounts/supabase/chats/",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            chats = data.get('chats', [])
            
            print(f"Number of chats: {len(chats)}")
            print("\n📊 Chat Analysis:")
            print("-" * 40)
            
            for i, chat in enumerate(chats, 1):
                print(f"\nChat {i}:")
                print(f"  ID: {chat.get('id')}")
                print(f"  Student ID: {chat.get('student_id')}")
                print(f"  Teacher ID: {chat.get('teacher_id')}")
                print(f"  Student Name: {chat.get('student_name')}")
                print(f"  Teacher Name: {chat.get('teacher_name')}")
                print(f"  Roles Identified: {chat.get('roles_identified')}")
                print(f"  Assignment Method: {chat.get('role_assignment_method')}")
                
                # Check user_info for detailed role information
                user_info = chat.get('user_info', {})
                print(f"  User Info:")
                for user_id, info in user_info.items():
                    role_source = info.get('role_source', 'unknown')
                    warning = info.get('warning', '')
                    print(f"    {user_id}: {info.get('name')} ({info.get('role')}) [source: {role_source}]")
                    if warning:
                        print(f"      ⚠️  {warning}")
                
                print(f"  Participants: {chat.get('participants', [])}")
                
                # Validate name-ID mapping
                student_id = chat.get('student_id')
                teacher_id = chat.get('teacher_id')
                student_name = chat.get('student_name')
                teacher_name = chat.get('teacher_name')
                
                if student_id in user_info and teacher_id in user_info:
                    expected_student_name = user_info[student_id]['name']
                    expected_teacher_name = user_info[teacher_id]['name']
                    
                    student_name_correct = student_name == expected_student_name
                    teacher_name_correct = teacher_name == expected_teacher_name
                    
                    print(f"  ✅ Name-ID Mapping:")
                    print(f"    Student: {'✓' if student_name_correct else '✗'} {student_name} -> {student_id}")
                    print(f"    Teacher: {'✓' if teacher_name_correct else '✗'} {teacher_name} -> {teacher_id}")
                    
                    if not (student_name_correct and teacher_name_correct):
                        print(f"    🚨 MAPPING ERROR DETECTED!")
                        print(f"       Expected student name: {expected_student_name}")
                        print(f"       Expected teacher name: {expected_teacher_name}")
        
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

def check_django_role_detection():
    """Check if Django role detection is working properly"""
    
    print("\n🔍 Testing Django Role Detection Logic")
    print("=" * 40)
    
    try:
        from accounts.models import TeacherProfile
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get some sample users
        users = User.objects.all()[:5]
        
        for user in users:
            has_teacher_profile = TeacherProfile.objects.filter(user=user).exists()
            detected_role = 'TEACHER' if has_teacher_profile else 'STUDENT'
            
            print(f"User: {user.email}")
            print(f"  Has Teacher Profile: {has_teacher_profile}")
            print(f"  Detected Role: {detected_role}")
            print()
    
    except Exception as e:
        print(f"❌ Error checking Django role detection: {e}")

def suggest_metadata_sync():
    """Suggest how to sync roles from Django to Supabase metadata"""
    
    print("\n💡 Metadata Sync Suggestions")
    print("=" * 30)
    print("""
To ensure consistent role detection, consider:

1. Create a management command to sync Django roles to Supabase:
   ```python
   # management/commands/sync_roles_to_supabase.py
   from django.core.management.base import BaseCommand
   from supabase import create_client
   
   class Command(BaseCommand):
       def handle(self, *args, **options):
           # Update Supabase user metadata with Django roles
   ```

2. Update roles during user registration/profile updates

3. Add a scheduled task to periodically sync roles

4. Consider adding a supabase_id field to your User model for better mapping
   """)

if __name__ == "__main__":
    print("🚀 Starting Improved Role Detection Tests")
    print("=" * 50)
    
    # Run tests
    test_improved_chats_endpoint()
    check_django_role_detection()
    suggest_metadata_sync()
    
    print("\n✅ Test completed!")
    print("\nNext steps:")
    print("1. Update the test_token variable with a valid token")
    print("2. Run the test to verify improved role detection")
    print("3. Check if Django role detection is working")
    print("4. Consider implementing metadata sync if needed")
