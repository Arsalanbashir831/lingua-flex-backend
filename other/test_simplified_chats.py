"""
Test script for simplified chats endpoint response
Tests that only essential fields are returned in participant details
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CHATS_URL = f"{BASE_URL}/accounts/supabase/chats/"

def test_simplified_chats_response():
    """Test the simplified chats endpoint response"""
    
    # You'll need to provide a valid access token (student or teacher)
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Simplified Chats Endpoint Response")
    print(f"URL: {CHATS_URL}")
    print("="*60)
    
    try:
        # Test GET request
        print("\n=== Fetching Simplified Chat Details ===")
        response = requests.get(CHATS_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            chats = response.json()
            print(f"✅ Request successful!")
            print(f"Found {len(chats)} chats")
            
            # Analyze the simplified response structure
            if chats:
                print(f"\n=== Simplified Response Analysis ===")
                
                for i, chat in enumerate(chats, 1):
                    print(f"\nChat {i}:")
                    print(f"  Chat ID: {chat.get('id')}")
                    print(f"  Created: {chat.get('created_at')}")
                    
                    # Check student details
                    student_details = chat.get('student_details')
                    if student_details:
                        print(f"  Student Details:")
                        print(f"    ID: {student_details.get('id')}")
                        print(f"    Name: {student_details.get('name')}")
                        print(f"    Email: {student_details.get('email')}")
                        print(f"    Role: {student_details.get('role')}")
                        print(f"    Profile Picture: {student_details.get('profile_picture') or 'None'}")
                        print(f"    Created At: {student_details.get('created_at')}")
                        
                        # Check for unwanted fields
                        unwanted_fields = ['bio', 'city', 'country', 'postal_code', 'phone_number', 
                                         'gender', 'date_of_birth', 'status', 'native_language', 
                                         'learning_language', 'full_name']
                        
                        found_unwanted = []
                        for field in unwanted_fields:
                            if field in student_details:
                                found_unwanted.append(field)
                        
                        if found_unwanted:
                            print(f"    ⚠️  Found unwanted fields: {found_unwanted}")
                        else:
                            print(f"    ✅ Only essential fields present")
                    
                    # Check teacher details
                    teacher_details = chat.get('teacher_details')
                    if teacher_details:
                        print(f"  Teacher Details:")
                        print(f"    ID: {teacher_details.get('id')}")
                        print(f"    Name: {teacher_details.get('name')}")
                        print(f"    Email: {teacher_details.get('email')}")
                        print(f"    Role: {teacher_details.get('role')}")
                        print(f"    Profile Picture: {teacher_details.get('profile_picture') or 'None'}")
                        print(f"    Created At: {teacher_details.get('created_at')}")
                        
                        # Check for unwanted fields
                        unwanted_fields = ['bio', 'city', 'country', 'postal_code', 'phone_number', 
                                         'gender', 'date_of_birth', 'native_language', 'learning_language',
                                         'qualification', 'experience_years', 'certificates', 'about', 'full_name']
                        
                        found_unwanted = []
                        for field in unwanted_fields:
                            if field in teacher_details:
                                found_unwanted.append(field)
                        
                        if found_unwanted:
                            print(f"    ⚠️  Found unwanted fields: {found_unwanted}")
                        else:
                            print(f"    ✅ Only essential fields present")
                
                # Show expected vs actual structure
                print(f"\n=== Expected vs Actual Structure ===")
                if chats:
                    sample_chat = chats[0]
                    
                    print("\nExpected participant details fields:")
                    expected_fields = ['id', 'name', 'email', 'role', 'profile_picture', 'created_at']
                    for field in expected_fields:
                        print(f"  ✅ {field}")
                    
                    print("\nActual student_details fields:")
                    if sample_chat.get('student_details'):
                        for field in sample_chat['student_details'].keys():
                            if field in expected_fields:
                                print(f"  ✅ {field}")
                            else:
                                print(f"  ❌ {field} (unexpected)")
                    
                    print("\nActual teacher_details fields:")
                    if sample_chat.get('teacher_details'):
                        for field in sample_chat['teacher_details'].keys():
                            if field in expected_fields:
                                print(f"  ✅ {field}")
                            else:
                                print(f"  ❌ {field} (unexpected)")
            
            else:
                print("No chats found. Create a chat first to test the simplified response.")
        
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your access token.")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def show_response_comparison():
    """Show the difference between previous and new simplified response"""
    
    print("\n" + "="*60)
    print("=== Response Format Comparison ===")
    
    print("\nBEFORE (Comprehensive Response):")
    print("""
"student_details": {
    "id": "ea65c360-49a9-460e-bab1-6e3f8b5c831e",
    "email": "novina5026@cotasen.com",
    "first_name": "Student1",
    "last_name": "Student2",
    "full_name": "Student1 Student2",
    "role": "STUDENT",
    "phone_number": "1234567890",
    "gender": "Male",
    "date_of_birth": "2000-01-05",
    "profile_picture": null,
    "created_at": "2025-08-08T04:40:56.743474Z",
    "bio": "I am a passionate language learner...",
    "city": "New York",
    "country": "United States",
    "postal_code": "10001",
    "status": "Active",
    "native_language": "English",
    "learning_language": "Spanish"
}""")
    
    print("\nAFTER (Simplified Response):")
    print("""
"student_details": {
    "id": "ea65c360-49a9-460e-bab1-6e3f8b5c831e",
    "name": "Student1 Student2",
    "email": "novina5026@cotasen.com",
    "role": "STUDENT",
    "profile_picture": null,
    "created_at": "2025-08-08T04:40:56.743474Z"
}""")
    
    print("\n=== Simplification Summary ===")
    print("✅ Reduced from 13+ fields to 6 essential fields")
    print("✅ Combined first_name and last_name into single 'name' field")
    print("✅ Removed personal details (phone, gender, date_of_birth)")
    print("✅ Removed profile information (bio, city, country, etc.)")
    print("✅ Removed role-specific details (qualifications, certificates, etc.)")
    print("✅ Kept only essential chat participant information")
    print("✅ Reduced response size significantly")

def test_different_scenarios():
    """Test different user scenarios with simplified response"""
    
    print("\n" + "="*60)
    print("=== Expected Simplified Response Scenarios ===")
    
    scenarios = [
        {
            "name": "Student participant",
            "expected_fields": ["id", "name", "email", "role", "profile_picture", "created_at"],
            "description": "Student details with only essential fields"
        },
        {
            "name": "Teacher participant",
            "expected_fields": ["id", "name", "email", "role", "profile_picture", "created_at"],
            "description": "Teacher details with only essential fields (no qualifications)"
        },
        {
            "name": "Missing profile picture",
            "expected_result": "profile_picture: null",
            "description": "Users without profile pictures show null"
        },
        {
            "name": "Error handling",
            "expected_result": "Graceful error response with essential fields",
            "description": "Missing profiles handled gracefully"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Description: {scenario['description']}")
        if 'expected_fields' in scenario:
            print(f"  Expected fields: {scenario['expected_fields']}")
        if 'expected_result' in scenario:
            print(f"  Expected result: {scenario['expected_result']}")

if __name__ == "__main__":
    print("=== Simplified Chats Endpoint Testing ===")
    
    print("\nThis test verifies that the chats endpoint now returns only:")
    print("- id: User unique identifier")
    print("- name: Combined first and last name")
    print("- email: User email address")
    print("- role: User role (STUDENT/TEACHER)")
    print("- profile_picture: Profile picture URL or null")
    print("- created_at: Account creation timestamp")
    
    print("\n" + "="*60)
    print("Setup Instructions:")
    print("1. Update the access_token variable with a valid token")
    print("2. Ensure you have at least one chat in Supabase")
    print("3. Ensure chat participants exist in Django User model")
    print("4. Run Django server: python manage.py runserver")
    print("="*60)
    
    # Show response format comparison
    show_response_comparison()
    
    # Show test scenarios
    test_different_scenarios()
    
    print(f"\n{'='*60}")
    print("To run the actual test, uncomment the function call below:")
    print("# test_simplified_chats_response()")
    
    # Uncomment to run actual test (after setting token)
    # test_simplified_chats_response()
