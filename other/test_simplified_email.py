"""
Test script for simplified teacher email notification with only student name and profile picture
"""
import requests
import json

# Configuration
FASTAPI_URL = "http://127.0.0.1:8001"
START_CHAT_URL = f"{FASTAPI_URL}/chats/start/"

def test_simplified_teacher_email():
    """Test that teacher receives email with only student name and profile picture"""
    
    # Test data for starting a chat
    test_data = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",  # Replace with actual student ID
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"   # Replace with actual teacher ID
    }
    
    print("Testing simplified teacher email notification...")
    print(f"URL: {START_CHAT_URL}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(START_CHAT_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat started successfully!")
            print(f"Chat ID: {result.get('id')}")
            print(f"Participant 1: {result.get('participant1')}")
            print(f"Participant 2: {result.get('participant2')}")
            print(f"Created at: {result.get('created_at')}")
            
            print("\n📧 Email Features:")
            print("- Teacher should receive email with:")
            print("  ✓ Student's name only")
            print("  ✓ Student's profile picture (if available)")
            print("  ✓ Chat link: http://localhost:3000/teacher/chat?chatId=" + str(result.get('id')))
            print("  ✓ No other student details (email, phone, etc.)")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server.")
        print("Make sure the server is running on http://127.0.0.1:8001")
        print("Start it with: uvicorn fastapi_chat:app --host 127.0.0.1 --port 8001 --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_email_template_structure():
    """Test the email template structure manually"""
    
    # Sample student data with profile picture
    student_details = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "profile_picture": "https://example.com/profile.jpg",
        "phone_number": "+1234567890",
        "country": "USA",
        "native_language": "English",
        "learning_language": "Spanish"
    }
    
    teacher_details = {
        "email": "teacher@example.com",
        "first_name": "Jane",
        "last_name": "Teacher"
    }
    
    chat_id = "12345"
    
    print("\n" + "="*60)
    print("Testing Email Template Structure")
    print("="*60)
    
    # Simulate the email content generation
    profile_picture_html = ""
    if student_details.get('profile_picture'):
        profile_picture_html = f"""
        <div style="text-align: center; margin: 20px 0;">
            <img src="{student_details.get('profile_picture')}" 
                 alt="Student Profile" 
                 style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #3498db;">
        </div>
        """
    
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
            <a href="http://localhost:3000/teacher/chat?chatId={chat_id}" 
               style="background-color: #3498db; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Open Chat Conversation
            </a>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <a href="http://localhost:3000/teacher/dashboard" 
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
    
    print("✅ Email Template Generated Successfully!")
    print(f"\nEmail Subject: New Chat Request from {student_details.get('first_name')} {student_details.get('last_name')}")
    print(f"Email To: {teacher_details.get('email')}")
    print(f"Chat Link: http://localhost:3000/teacher/chat?chatId={chat_id}")
    
    print(f"\n📋 Email Content Summary:")
    print(f"- Student Name: {student_details.get('first_name')} {student_details.get('last_name')}")
    print(f"- Profile Picture: {'✓ Included' if student_details.get('profile_picture') else '✗ Not available'}")
    print(f"- Other Details: ✗ Excluded (email, phone, country, etc.)")
    print(f"- Chat Link: ✓ Included")
    print(f"- Dashboard Link: ✓ Included")
    
    # Save template to file for inspection
    with open("email_template_preview.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n💾 Email template saved to: email_template_preview.html")

if __name__ == "__main__":
    print("Simplified Teacher Email Notification Test")
    print("="*50)
    
    # Test the email template structure
    test_email_template_structure()
    
    print("\n" + "="*50)
    print("To test with real API:")
    print("1. Start FastAPI server: uvicorn fastapi_chat:app --host 127.0.0.1 --port 8001 --reload")
    print("2. Update student_id and teacher_id with real IDs")
    print("3. Uncomment the function call below")
    print("="*50)
    
    # Uncomment to test with real API
    # test_simplified_teacher_email()
