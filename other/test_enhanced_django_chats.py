"""
Test script for enhanced Django chats endpoint
Tests that the endpoint now returns structured teacher/student information
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CHATS_URL = f"{BASE_URL}/accounts/supabase/chats/"

def test_enhanced_chats_endpoint():
    """Test the enhanced chats endpoint"""
    
    # You'll need to provide a valid access token for testing
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Enhanced Django Chats Endpoint")
    print(f"URL: {CHATS_URL}")
    print("="*60)
    
    try:
        print("\n=== Test 1: Getting User's Chats ===")
        response = requests.get(CHATS_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            chats = response.json()
            print("✅ Chats endpoint successful!")
            print(f"Found {len(chats)} chats")
            
            if chats:
                print(f"\nFirst chat structure:")
                first_chat = chats[0]
                print(json.dumps(first_chat, indent=2))
                
                # Verify the enhanced structure
                expected_fields = ['id', 'student_id', 'teacher_id', 'student_name', 'teacher_name', 'created_at']
                missing_fields = []
                
                for field in expected_fields:
                    if field not in first_chat:
                        missing_fields.append(field)
                
                if not missing_fields:
                    print("\n✅ All expected fields present!")
                    print(f"Chat ID: {first_chat['id']}")
                    print(f"Student: {first_chat['student_name']} (ID: {first_chat['student_id']})")
                    print(f"Teacher: {first_chat['teacher_name']} (ID: {first_chat['teacher_id']})")
                    print(f"Created: {first_chat['created_at']}")
                    
                    if 'roles_identified' in first_chat:
                        print(f"Roles identified: {first_chat['roles_identified']}")
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                
                # Check if old fields are gone
                old_fields = ['participant1', 'participant2']
                found_old_fields = [field for field in old_fields if field in first_chat]
                
                if found_old_fields:
                    print(f"⚠️  Old fields still present: {found_old_fields}")
                else:
                    print("✅ Old participant1/participant2 fields removed!")
                
                # Show all chats summary
                print(f"\n=== All Chats Summary ===")
                for i, chat in enumerate(chats, 1):
                    print(f"{i}. {chat.get('student_name', 'N/A')} ↔ {chat.get('teacher_name', 'N/A')}")
                    print(f"   ID: {chat['id']}")
                    print(f"   Roles OK: {chat.get('roles_identified', 'Unknown')}")
                    if 'error' in chat:
                        print(f"   Error: {chat['error']}")
                    print()
            else:
                print("ℹ️  No chats found for this user")
                
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your access token.")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running on port 8000.")
        print("Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_different_users():
    """Test with different user tokens to see different perspectives"""
    
    print("\n" + "="*60)
    print("=== Testing Different User Perspectives ===")
    
    # You can add multiple test tokens here
    test_users = [
        {
            "name": "User 1",
            "token": "USER_1_TOKEN_HERE"  # Replace with actual token
        },
        {
            "name": "User 2", 
            "token": "USER_2_TOKEN_HERE"  # Replace with actual token
        }
    ]
    
    for user in test_users:
        print(f"\n--- Testing as {user['name']} ---")
        
        headers = {
            "Authorization": f"Bearer {user['token']}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(CHATS_URL, headers=headers)
            
            if response.status_code == 200:
                chats = response.json()
                print(f"✅ {len(chats)} chats found for {user['name']}")
                
                for chat in chats:
                    print(f"   - {chat.get('student_name', 'N/A')} ↔ {chat.get('teacher_name', 'N/A')}")
            else:
                print(f"❌ Failed for {user['name']}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error for {user['name']}: {e}")

def compare_old_vs_new_format():
    """Show comparison between old and new response format"""
    
    print("\n" + "="*60)
    print("=== Response Format Comparison ===")
    
    print("\n--- OLD Response Format ---")
    old_response = [
        {
            "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
            "participant1": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
            "participant2": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
            "created_at": "2025-08-06T10:19:14.395377+00:00"
        }
    ]
    print(json.dumps(old_response, indent=2))
    
    print("\n--- NEW Response Format ---")
    new_response = [
        {
            "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
            "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
            "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
            "student_name": "John Doe",
            "teacher_name": "Jane Smith",
            "created_at": "2025-08-06T10:19:14.395377+00:00",
            "roles_identified": True
        }
    ]
    print(json.dumps(new_response, indent=2))
    
    print("\n--- Key Changes ---")
    print("✅ Added: student_id, teacher_id (clear role identification)")
    print("✅ Added: student_name, teacher_name (human-readable names)")
    print("✅ Added: roles_identified (indicates if roles were properly detected)")
    print("❌ Removed: participant1, participant2 (unclear roles)")
    print("🔄 Enhanced: Role detection based on user metadata")

def test_error_handling():
    """Test error scenarios"""
    
    print("\n" + "="*60)
    print("=== Testing Error Scenarios ===")
    
    # Test without authentication
    print("\n--- Test without authentication ---")
    try:
        response = requests.get(CHATS_URL)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Properly requires authentication")
        else:
            print(f"⚠️  Expected 401, got {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test with invalid token
    print("\n--- Test with invalid token ---")
    invalid_headers = {
        "Authorization": "Bearer invalid_token_here",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(CHATS_URL, headers=invalid_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Properly rejects invalid tokens")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=== Enhanced Django Chats Endpoint Testing ===")
    
    # Show the expected changes
    compare_old_vs_new_format()
    
    print("\n" + "="*60)
    print("Setup Instructions:")
    print("1. Update the access_token variable with a valid user token")
    print("2. Make sure Django server is running: python manage.py runserver")
    print("3. Ensure Supabase credentials are configured in Django settings")
    print("4. Test users should exist in Supabase auth with proper metadata")
    print("="*60)
    
    # Run the main test
    test_enhanced_chats_endpoint()
    
    # Additional tests
    test_error_handling()
    
    # Uncomment to test with multiple users
    # test_with_different_users()
    
    print("\n" + "="*60)
    print("To test with actual data:")
    print("1. Replace 'YOUR_ACCESS_TOKEN_HERE' with a valid token")
    print("2. Ensure the user has existing chats in the database")
    print("3. Run the script to verify the enhanced format")
    print("="*60)
