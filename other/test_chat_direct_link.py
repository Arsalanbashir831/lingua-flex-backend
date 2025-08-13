"""
Test script for chat start with direct chat link in teacher email
"""
import requests
import json

# FastAPI server URL
FASTAPI_URL = "http://127.0.0.1:8001"
CHAT_START_URL = f"{FASTAPI_URL}/chats/start/"

def test_chat_start_with_direct_link():
    """Test starting a chat and verify email contains direct chat link"""
    
    # Test data - replace with actual user IDs from your database
    test_data = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",  # Replace with actual student ID
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"   # Replace with actual teacher ID
    }
    
    print("Testing Chat Start with Direct Chat Link in Email")
    print(f"URL: {CHAT_START_URL}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(CHAT_START_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat started successfully!")
            
            chat_id = result.get('id')
            print(f"Chat ID: {chat_id}")
            print(f"Participant 1: {result.get('participant1')}")
            print(f"Participant 2: {result.get('participant2')}")
            print(f"Created At: {result.get('created_at')}")
            
            # Show the expected chat link
            expected_link = f"http://localhost:3000/teacher/chat?chatId={chat_id}"
            print(f"\n📧 Email should contain this direct chat link:")
            print(f"🔗 {expected_link}")
            
            print(f"\n📝 Verification checklist:")
            print(f"✅ Chat ID {chat_id} should be in the email")
            print(f"✅ Link should redirect teacher directly to this chat")
            print(f"✅ Primary button: 'Open Chat Conversation'")
            print(f"✅ Secondary button: 'Go to LinguaFlex Dashboard'")
            print(f"✅ Student details should be included")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server.")
        print("Make sure the server is running with: uvicorn fastapi_chat:app --host 127.0.0.1 --port 8001 --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_expected_email_format():
    """Show the expected email format with chat link"""
    
    print("\n" + "="*60)
    print("Expected Email Content with Direct Chat Link")
    print("-" * 60)
    
    email_template = """
    From: LinguaFlex <onboarding@lordevs.com>
    To: [Teacher Email]
    Subject: New Chat Request from [Student Name]
    
    📱 A student has initiated a chat conversation with you!
    
    Student Details:
    - Name: [Student Name]
    - Email: [Student Email]
    - Role: Student
    - Country: [Country]
    - Native Language: [Language]
    - Learning Language: [Language]
    
    [PRIMARY BUTTON: "Open Chat Conversation"]
    Link: http://localhost:3000/teacher/chat?chatId=[CHAT_ID]
    
    [SECONDARY BUTTON: "Go to LinguaFlex Dashboard"]
    Link: http://127.0.0.1:8000
    
    This is an automated notification from LinguaFlex.
    """
    
    print(email_template)
    
    print("\nKey Improvements:")
    print("✅ Direct link to specific chat conversation")
    print("✅ Chat ID dynamically included in URL")
    print("✅ Teacher can join chat with one click")
    print("✅ No need to search for the conversation")
    print("✅ Better user experience for teachers")

if __name__ == "__main__":
    print("=== Chat Direct Link Email Test ===")
    
    show_expected_email_format()
    
    print(f"\n{'='*60}")
    print("Running Test...")
    print("Update student_id and teacher_id with real values")
    print("Make sure FastAPI server is running on port 8001")
    print("="*60)
    
    # Run the test
    test_chat_start_with_direct_link()
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print("Check teacher's email for the direct chat link.")
    print("="*60)
