"""
Test script to verify that the gigs endpoint returns teacher details
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
GIGS_URL = f"{BASE_URL}/accounts/gigs/"
PUBLIC_GIGS_URL = f"{BASE_URL}/accounts/gigs/public/"

def test_gigs_with_teacher_details():
    """Test gigs endpoint to verify teacher details are included"""
    
    # You'll need to provide a valid access token for a teacher
    access_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing gigs endpoint with teacher details...")
    print(f"URL: {GIGS_URL}")
    
    try:
        # Test POST request to create a gig
        print("\n=== Testing POST request (Create Gig) ===")
        test_gig_data = {
            "category": "language",
            "service_type": "Language Consultation",
            "service_title": "1-on-1 English Conversation",
            "short_description": "Improve your spoken English in a friendly session.",
            "full_description": "We will focus on fluency, pronunciation, and confidence.",
            "price_per_session": "25.00",
            "session_duration": 60,
            "tags": ["english", "conversation"],
            "what_you_provide_in_session": "Personalized feedback and practice"
        }
        
        response = requests.post(GIGS_URL, json=test_gig_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("✅ POST request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if teacher_details is present
            if 'teacher_details' in data:
                teacher_details = data['teacher_details']
                print(f"✅ Teacher details found!")
                
                # Check for expected teacher fields
                expected_fields = [
                    'id', 'user_id', 'email', 'first_name', 'last_name', 
                    'full_name', 'profile_picture', 'qualification', 
                    'experience_years', 'about', 'bio', 'city', 'country'
                ]
                
                missing_fields = []
                for field in expected_fields:
                    if field not in teacher_details:
                        missing_fields.append(field)
                    else:
                        print(f"  ✅ {field}: {teacher_details[field]}")
                
                if missing_fields:
                    print(f"❌ Missing teacher detail fields: {missing_fields}")
                else:
                    print("✅ All teacher detail fields are present!")
                    
            else:
                print("❌ teacher_details field not found in response")
                
        else:
            print(f"❌ POST request failed: {response.text}")
        
        # Test GET request for existing gigs
        print("\n=== Testing GET request (List Gigs) ===")
        response = requests.get(GIGS_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GET request successful!")
            
            if isinstance(data, list) and len(data) > 0:
                first_gig = data[0]
                print(f"First gig: {json.dumps(first_gig, indent=2)}")
                
                if 'teacher_details' in first_gig:
                    print("✅ Teacher details present in GET response!")
                else:
                    print("❌ Teacher details missing in GET response")
            else:
                print("ℹ️ No gigs found in response")
                
        else:
            print(f"❌ GET request failed: {response.text}")
        
        # Test PUBLIC gigs endpoint
        print("\n=== Testing PUBLIC Gigs Endpoint ===")
        response = requests.get(PUBLIC_GIGS_URL)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Public gigs request successful!")
            
            if isinstance(data, list) and len(data) > 0:
                first_gig = data[0]
                if 'teacher_details' in first_gig:
                    print("✅ Teacher details present in public gigs!")
                    print(f"Teacher: {first_gig['teacher_details'].get('full_name', 'N/A')}")
                else:
                    print("❌ Teacher details missing in public gigs")
            else:
                print("ℹ️ No public gigs found")
                
        else:
            print(f"❌ Public gigs request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def get_teacher_access_token():
    """Helper function to get teacher access token"""
    print("To test the gigs endpoint, you need a teacher account:")
    print("1. First login as a teacher to get an access token")
    print("2. Replace 'YOUR_TEACHER_ACCESS_TOKEN_HERE' in the script")
    print("3. Run this script again")
    
    # Example login request for teacher
    login_data = {
        "email": "teacher@example.com",  # Replace with actual teacher email
        "password": "teacherpassword"    # Replace with actual teacher password
    }
    
    try:
        login_url = f"{BASE_URL}/api/auth/login/"
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            user_role = data.get('user', {}).get('role')
            
            if user_role == 'TEACHER':
                print(f"\n✅ Teacher login successful! Access token: {data.get('access_token', 'Not found')}")
                return data.get('access_token')
            else:
                print(f"❌ User role is {user_role}, but TEACHER role is required")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    return None

if __name__ == "__main__":
    print("=== Gigs with Teacher Details Testing ===")
    
    # First try to get teacher access token
    token = get_teacher_access_token()
    
    if token:
        print(f"\nUse this token in the test function: {token}")
    
    print("\n" + "="*60)
    print("Manual Testing Instructions:")
    print("1. Update the access_token variable in test_gigs_with_teacher_details()")
    print("2. Update login credentials in get_teacher_access_token() if needed")
    print("3. Ensure you have a teacher account with proper profile setup")
    print("4. Run: test_gigs_with_teacher_details()")
    print("="*60)
    
    # Uncomment this line after setting the correct token
    # test_gigs_with_teacher_details()
