"""
Test script for the improved registration endpoint
Tests different scenarios: new user, existing verified user, existing unverified user
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
REGISTER_URL = f"{BASE_URL}/api/accounts/register/"

def test_registration_scenarios():
    """Test various registration scenarios"""
    
    test_cases = [
        {
            "name": "New User Registration",
            "description": "Test registering a completely new user",
            "data": {
                "email": "newuser@example.com",
                "password": "testpassword123", 
                "full_name": "New User",
                "role": "STUDENT"
            },
            "expected_status": 201,
            "expected_message": "Registration successful"
        },
        {
            "name": "Existing Verified User",
            "description": "Test attempting to register with an existing verified email",
            "data": {
                "email": "verified@example.com",  # Use an email that's already verified
                "password": "testpassword123",
                "full_name": "Verified User", 
                "role": "STUDENT"
            },
            "expected_status": 409,
            "expected_message": "User already exists and is verified"
        },
        {
            "name": "Existing Unverified User",
            "description": "Test attempting to register with an existing unverified email",
            "data": {
                "email": "unverified@example.com",  # Use an email that exists but unverified
                "password": "testpassword123",
                "full_name": "Unverified User",
                "role": "STUDENT" 
            },
            "expected_status": 200,
            "expected_message": "Verification email resent"
        },
        {
            "name": "Teacher Registration",
            "description": "Test registering a new teacher",
            "data": {
                "email": "newteacher@example.com",
                "password": "testpassword123",
                "full_name": "New Teacher",
                "role": "TEACHER",
                "qualification": "PhD in English",
                "experience_years": 5,
                "about": "Experienced English teacher"
            },
            "expected_status": 201,
            "expected_message": "Registration successful"
        }
    ]
    
    print("Testing Registration Endpoint with Different Scenarios")
    print(f"URL: {REGISTER_URL}")
    print("=" * 70)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Test Data: {json.dumps(test_case['data'], indent=6)}")
        
        try:
            response = requests.post(REGISTER_URL, json=test_case['data'])
            
            print(f"   Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"   Response: {json.dumps(response_data, indent=6)}")
                
                # Check if response matches expectations
                if response.status_code == test_case['expected_status']:
                    print(f"   ✅ Status code matches expected ({test_case['expected_status']})")
                else:
                    print(f"   ❌ Status code mismatch. Expected: {test_case['expected_status']}, Got: {response.status_code}")
                
                # Check if response contains expected message
                response_text = json.dumps(response_data).lower()
                expected_text = test_case['expected_message'].lower()
                if expected_text in response_text:
                    print(f"   ✅ Response contains expected message")
                else:
                    print(f"   ❌ Response doesn't contain expected message: '{test_case['expected_message']}'")
                    
            except json.JSONDecodeError:
                print(f"   Response Text: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to server. Make sure Django server is running.")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 50)

def test_your_specific_case():
    """Test the exact case you mentioned"""
    
    print("\n" + "=" * 70)
    print("Testing Your Specific Case")
    print("=" * 70)
    
    your_data = {
        "email": "novina5026@cotasen.com",
        "password": "testpassword123",
        "full_name": "Jane Student",
        "role": "STUDENT"
    }
    
    print(f"Request Data: {json.dumps(your_data, indent=2)}")
    print(f"URL: {REGISTER_URL}")
    
    try:
        response = requests.post(REGISTER_URL, json=your_data)
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            # Analyze the response
            if response.status_code == 201:
                print("✅ New user registered successfully!")
            elif response.status_code == 409:
                print("✅ User already exists and is verified - login instead")
            elif response.status_code == 200:
                print("✅ User exists but unverified - verification email resent")
            else:
                print(f"❓ Unexpected response: {response.status_code}")
                
        except json.JSONDecodeError:
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_api_documentation():
    """Show the updated API documentation"""
    
    print("\n" + "=" * 70)
    print("UPDATED REGISTRATION API DOCUMENTATION")
    print("=" * 70)
    
    print("""
ENDPOINT: POST /api/accounts/register/

BEHAVIOR:
1. If user does NOT exist:
   - Create new user in Supabase and Django
   - Send verification email
   - Return 201 Created

2. If user exists and IS VERIFIED:
   - Return 409 Conflict
   - Message: "User already exists and is verified. Please login instead."

3. If user exists but NOT VERIFIED:
   - Resend verification email
   - Return 200 OK
   - Message: "User exists but not verified. Verification email resent."

REQUEST FORMAT:
{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Full Name",
    "role": "STUDENT" or "TEACHER",
    
    // Optional fields for teachers:
    "qualification": "PhD in Subject",
    "experience_years": 5,
    "about": "Teacher description",
    "bio": "Short bio",
    "city": "City Name",
    "country": "Country Name",
    "native_language": "English",
    "learning_language": "Spanish"
}

RESPONSE EXAMPLES:

1. New User (201 Created):
{
    "message": "Registration successful. Please verify your email."
}

2. Existing Verified User (409 Conflict):
{
    "error": "User already exists and is verified. Please login instead.",
    "action": "login"
}

3. Existing Unverified User (200 OK):
{
    "message": "User exists but not verified. Verification email resent.",
    "action": "verify_email"
}

4. Registration Failed (400 Bad Request):
{
    "error": "Registration failed"
}
""")

if __name__ == "__main__":
    print("Registration Endpoint Test Suite")
    print("Make sure Django server is running on http://127.0.0.1:8000")
    
    # Show updated documentation
    show_api_documentation()
    
    # Test your specific case
    test_your_specific_case()
    
    # Test various scenarios
    # test_registration_scenarios()
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("Note: Some test cases require existing users in the database to work properly.")
    print("=" * 70)
