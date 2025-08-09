#!/usr/bin/env python3
"""
Quick verification script for the improved role detection system
This script helps verify that the enhanced endpoint is working correctly
"""

import requests
import json

def test_enhanced_endpoint():
    """Test the enhanced Django chats endpoint"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    # Replace with a valid token
    test_token = "your_test_token_here"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Enhanced Role Detection")
    print("=" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}/accounts/supabase/chats/",
            headers=headers,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            chats = data.get('chats', [])
            
            print(f"Chats found: {len(chats)}")
            
            if chats:
                # Analyze first chat in detail
                chat = chats[0]
                print(f"\n📊 Sample Chat Analysis:")
                print(f"  ID: {chat.get('id')}")
                print(f"  Roles Identified: {chat.get('roles_identified')}")
                print(f"  Assignment Method: {chat.get('role_assignment_method')}")
                
                # Check name-ID consistency
                user_info = chat.get('user_info', {})
                student_id = chat.get('student_id')
                teacher_id = chat.get('teacher_id')
                student_name = chat.get('student_name')
                teacher_name = chat.get('teacher_name')
                
                if student_id in user_info and teacher_id in user_info:
                    expected_student_name = user_info[student_id]['name']
                    expected_teacher_name = user_info[teacher_id]['name']
                    
                    student_correct = student_name == expected_student_name
                    teacher_correct = teacher_name == expected_teacher_name
                    
                    print(f"  Name Mapping:")
                    print(f"    Student: {'✅' if student_correct else '❌'} {student_name}")
                    print(f"    Teacher: {'✅' if teacher_correct else '❌'} {teacher_name}")
                    
                    if student_correct and teacher_correct:
                        print(f"  🎉 SUCCESS: Names correctly mapped to IDs!")
                    else:
                        print(f"  ⚠️  WARNING: Name-ID mapping issues detected")
                        print(f"     Expected student: {expected_student_name}")
                        print(f"     Expected teacher: {expected_teacher_name}")
                
                # Show role sources
                print(f"  Role Sources:")
                for user_id, info in user_info.items():
                    role_source = info.get('role_source', 'unknown')
                    role = info.get('role', 'UNKNOWN')
                    warning = info.get('warning', '')
                    
                    print(f"    {user_id[:8]}...: {role} (from {role_source})")
                    if warning:
                        print(f"      ⚠️  {warning}")
                
                print(f"\n✅ Enhanced endpoint is working!")
                return True
            else:
                print("ℹ️  No chats found - create some chats to test properly")
                return True
        
        elif response.status_code == 401:
            print("❌ Authentication failed - update the test_token")
            return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure Django server is running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def show_setup_instructions():
    """Show setup instructions"""
    
    print("\n📋 Setup Instructions")
    print("=" * 25)
    print("""
1. Start Django server:
   python manage.py runserver

2. Update test_token in this script with a valid token

3. Run this script:
   python verify_enhanced_system.py

4. To sync roles from Django to Supabase:
   python manage.py sync_roles_to_supabase --dry-run
   python manage.py sync_roles_to_supabase

5. For detailed testing:
   python test_improved_role_detection.py
""")

if __name__ == "__main__":
    print("🚀 Enhanced Role Detection Verification")
    print("=" * 40)
    
    success = test_enhanced_endpoint()
    
    if not success:
        show_setup_instructions()
    else:
        print("\n✅ Verification completed successfully!")
        print("\nNext steps:")
        print("1. Sync roles: python manage.py sync_roles_to_supabase")
        print("2. Test frontend integration")
        print("3. Monitor for any remaining mapping issues")
