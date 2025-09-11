"""
Test script to verify correct name mapping in Django chats endpoint
Tests that student_name corresponds to student_id and teacher_name corresponds to teacher_id
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CHATS_URL = f"{BASE_URL}/accounts/supabase/chats/"

def test_name_id_mapping():
    """Test that names are correctly mapped to their corresponding IDs"""
    
    # You'll need to provide a valid access token for testing
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Name-ID Mapping in Django Chats Endpoint")
    print(f"URL: {CHATS_URL}")
    print("="*60)
    
    try:
        print("\n=== Test: Name-ID Correspondence ===")
        response = requests.get(CHATS_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            chats = response.json()
            print("✅ Chats endpoint successful!")
            print(f"Found {len(chats)} chats")
            
            if chats:
                for i, chat in enumerate(chats, 1):
                    print(f"\n--- Chat {i} ---")
                    print(f"Chat ID: {chat['id']}")
                    print(f"Student ID: {chat['student_id']}")
                    print(f"Student Name: {chat['student_name']}")
                    print(f"Teacher ID: {chat['teacher_id']}")
                    print(f"Teacher Name: {chat['teacher_name']}")
                    print(f"Roles Identified: {chat['roles_identified']}")
                    
                    # Check if user_info is included for debugging
                    if 'user_info' in chat:
                        print(f"\nDetailed User Info:")
                        user_info = chat['user_info']
                        
                        for user_id, info in user_info.items():
                            print(f"  {user_id}: {info['name']} (Role: {info['role']})")
                        
                        # Verify correct mapping
                        student_actual_name = user_info.get(chat['student_id'], {}).get('name', 'NOT_FOUND')
                        teacher_actual_name = user_info.get(chat['teacher_id'], {}).get('name', 'NOT_FOUND')
                        
                        print(f"\nMapping Verification:")
                        print(f"  Student ID {chat['student_id']} should have name: {student_actual_name}")
                        print(f"  Returned student_name: {chat['student_name']}")
                        print(f"  ✅ Match: {student_actual_name == chat['student_name']}")
                        
                        print(f"  Teacher ID {chat['teacher_id']} should have name: {teacher_actual_name}")
                        print(f"  Returned teacher_name: {chat['teacher_name']}")
                        print(f"  ✅ Match: {teacher_actual_name == chat['teacher_name']}")
                        
                        if student_actual_name == chat['student_name'] and teacher_actual_name == chat['teacher_name']:
                            print("  🎉 CORRECT: Names match their respective IDs!")
                        else:
                            print("  ❌ ERROR: Name-ID mismatch detected!")
                    
                    if 'error' in chat:
                        print(f"Error: {chat['error']}")
                    
                    print("-" * 40)
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

def test_specific_ids():
    """Test with known user IDs to verify mapping"""
    
    print("\n" + "="*60)
    print("=== Testing with Known IDs ===")
    
    # From your example
    known_ids = {
        "a6e13d11-9bd4-4561-9e0b-0d199670d49e": "Should be student",
        "30139770-0d26-4e9e-8b36-8efb33ed7b2e": "Should be teacher"
    }
    
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(CHATS_URL, headers=headers)
        
        if response.status_code == 200:
            chats = response.json()
            
            for chat in chats:
                print(f"\nChat ID: {chat['id']}")
                
                # Check if the known IDs are in this chat
                if chat['student_id'] in known_ids or chat['teacher_id'] in known_ids:
                    print("Found chat with known IDs!")
                    
                    if chat['student_id'] == "a6e13d11-9bd4-4561-9e0b-0d199670d49e":
                        print(f"✅ Student ID matches expected: {chat['student_id']}")
                        print(f"Student name: {chat['student_name']}")
                    
                    if chat['teacher_id'] == "30139770-0d26-4e9e-8b36-8efb33ed7b2e":
                        print(f"✅ Teacher ID matches expected: {chat['teacher_id']}")
                        print(f"Teacher name: {chat['teacher_name']}")
                    
                    # This should help identify if the names are now correct
                    if 'user_info' in chat:
                        print("Raw user data:")
                        for uid, info in chat['user_info'].items():
                            print(f"  {uid}: {info['name']} (Role: {info['role']})")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def show_expected_vs_actual():
    """Show what should happen vs what was happening"""
    
    print("\n" + "="*60)
    print("=== Expected vs Previous Behavior ===")
    
    print("\n--- Previous Behavior (INCORRECT) ---")
    previous_wrong = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e", 
        "student_name": "Jane Student",  # WRONG: This is actually teacher's name
        "teacher_name": "John Jane",     # WRONG: This is actually student's name
        "roles_identified": False
    }
    print(json.dumps(previous_wrong, indent=2))
    
    print("\n--- Expected Behavior (CORRECT) ---")
    expected_correct = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
        "student_name": "Actual name for ID a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_name": "Actual name for ID 30139770-0d26-4e9e-8b36-8efb33ed7b2e",
        "roles_identified": True  # or False, but names should be correct regardless
    }
    print(json.dumps(expected_correct, indent=2))
    
    print("\n--- Key Fix ---")
    print("✅ Names now correctly correspond to their respective IDs")
    print("✅ student_name is the actual name of the user with student_id")
    print("✅ teacher_name is the actual name of the user with teacher_id") 
    print("✅ Role detection failure doesn't affect name mapping accuracy")

def debug_name_extraction():
    """Help debug name extraction logic"""
    
    print("\n" + "="*60)
    print("=== Debugging Name Extraction ===")
    
    print("The updated logic now:")
    print("1. Fetches user data for both participants")
    print("2. Extracts names independently for each user")
    print("3. Creates a mapping of user_id -> {name, role}")
    print("4. Assigns roles based on metadata")
    print("5. Maps names correctly to their respective IDs")
    print("\nName extraction priority:")
    print("1. first_name + last_name from metadata")
    print("2. first_name only (if last_name missing)")
    print("3. last_name only (if first_name missing)")
    print("4. Email username (part before @)")
    print("5. Generic fallback (User1/User2)")

if __name__ == "__main__":
    print("=== Name-ID Mapping Verification Test ===")
    
    # Show the problem and solution
    show_expected_vs_actual()
    
    # Show debugging info
    debug_name_extraction()
    
    print("\n" + "="*60)
    print("Setup Instructions:")
    print("1. Update the access_token variable with a valid user token")
    print("2. Make sure Django server is running: python manage.py runserver")
    print("3. Ensure the test user has the problematic chat")
    print("4. Run the test to verify names are now correctly mapped")
    print("="*60)
    
    # Run the main test
    test_name_id_mapping()
    
    # Test with known IDs
    test_specific_ids()
    
    print("\n" + "="*60)
    print("If names are still incorrect after this fix:")
    print("1. Check the 'user_info' field in the response")
    print("2. Verify that Supabase user metadata contains correct names")
    print("3. Check if role detection is working properly")
    print("4. Ensure user IDs in the chat correspond to actual users")
    print("="*60)
