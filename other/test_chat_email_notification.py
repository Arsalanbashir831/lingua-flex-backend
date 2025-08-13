"""
Test script for chat start with teacher email notification
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8001"
CHAT_START_URL = f"{BASE_URL}/chats/start/"

def test_chat_start_with_email_notification():
    """Test starting a chat and verify teacher email notification is sent"""
    
    print("Testing Chat Start with Teacher Email Notification")
    print("="*60)
    
    # Test data - replace with actual user IDs from your database
    test_data = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",  # Replace with actual student ID
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"   # Replace with actual teacher ID
    }
    
    print(f"URL: {CHAT_START_URL}")
    print(f"Payload: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(CHAT_START_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat started successfully!")
            print(f"Chat ID: {result.get('id')}")
            print(f"Participant 1: {result.get('participant1')}")
            print(f"Participant 2: {result.get('participant2')}")
            print(f"Created At: {result.get('created_at')}")
            
            print("\n📧 Check the teacher's email for notification!")
            print("The email should contain:")
            print("- Student details (name, email, role, etc.)")
            print("- Link to LinguaFlex dashboard")
            print("- Professional formatting")
            
        elif response.status_code == 422:
            error_data = response.json()
            print("❌ Validation Error:")
            print(json.dumps(error_data, indent=2))
            
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server.")
        print("Make sure the FastAPI chat server is running on port 8001:")
        print("uvicorn fastapi_chat:app --reload --port 8001")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_existing_chat():
    """Test starting a chat that already exists (should not send email)"""
    
    print("\n" + "="*60)
    print("Testing Existing Chat (No Email Should Be Sent)")
    print("="*60)
    
    # Same test data as above - should return existing chat
    test_data = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
    }
    
    try:
        response = requests.post(CHAT_START_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Existing chat returned successfully!")
            print(f"Chat ID: {result.get('id')}")
            print("📧 No email should be sent for existing chats")
            
        else:
            print(f"❌ Unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_invalid_user_ids():
    """Test with invalid user IDs"""
    
    print("\n" + "="*60)
    print("Testing Invalid User IDs")
    print("="*60)
    
    test_data = {
        "student_id": "invalid-student-id",
        "teacher_id": "invalid-teacher-id"
    }
    
    try:
        response = requests.post(CHAT_START_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("⚠️  Chat created but user details may not be found")
            print(f"Chat ID: {result.get('id')}")
            print("📧 Email notification may fail due to invalid user IDs")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Chat Start Email Notification Test Suite")
    print("\nBefore running this test:")
    print("1. Make sure FastAPI chat server is running: uvicorn fastapi_chat:app --reload --port 8001")
    print("2. Update the student_id and teacher_id with real UUIDs from your database")
    print("3. Ensure the teacher has a valid email address")
    print("4. Check that Resend API key is valid")
    
    print("\n" + "="*80)
    
    # Run tests
    test_chat_start_with_email_notification()
    test_existing_chat()
    test_invalid_user_ids()
    
    print("\n" + "="*80)
    print("Test Summary:")
    print("✅ New chat creation should send email to teacher")
    print("✅ Existing chat should NOT send email")
    print("✅ Invalid user IDs should handle gracefully")
    print("\nCheck the FastAPI server logs for email sending status messages")
