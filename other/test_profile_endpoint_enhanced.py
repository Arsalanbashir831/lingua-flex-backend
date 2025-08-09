"""
Test script to verify that the profile endpoint returns role, profile_picture, and created_at
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PROFILE_URL = f"{BASE_URL}/accounts/profiles/me/"

def test_profile_endpoint_with_new_fields():
    """Test profile endpoint to verify new fields are returned"""
    
    # You'll need to provide a valid access token for testing
    # You can get this from the login endpoint
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing profile endpoint with new fields...")
    print(f"URL: {PROFILE_URL}")
    
    try:
        # Test GET request first
        print("\n=== Testing GET request ===")
        response = requests.get(PROFILE_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GET request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if new fields are present
            expected_fields = ['id', 'email', 'role', 'profile_picture', 'created_at']
            missing_fields = []
            
            for field in expected_fields:
                if field not in data:
                    missing_fields.append(field)
                else:
                    print(f"✅ {field}: {data[field]}")
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print("✅ All new fields are present!")
                
        else:
            print(f"❌ GET request failed: {response.text}")
        
        # Test PATCH request
        print("\n=== Testing PATCH request ===")
        test_data = {
            "first_name": "Ching",
            "last_name": "Chang",
            "phone_number": "12345678905",
            "gender": "Male5",
            "date_of_birth": "2000-01-05",
            "bio": "I am a passionate language learner interested in improving my communication skills.",
            "city": "New York",
            "country": "United States",
            "postal_code": "10001",
            "status": "Active",
            "native_language": "English",
            "learning_language": "Spanish"
        }
        
        response = requests.patch(PROFILE_URL, json=test_data, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PATCH request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
                # Check if new fields are present in the response
                if 'profile' in data:
                    profile_data = data['profile']
                    expected_fields = ['id', 'email', 'role', 'profile_picture', 'created_at']
                    missing_fields = []
                    
                    for field in expected_fields:
                        if field not in profile_data:
                            missing_fields.append(field)
                        else:
                            print(f"✅ {field}: {profile_data[field]}")
                    
                    if missing_fields:
                        print(f"❌ Missing fields in profile: {missing_fields}")
                    else:
                        print("✅ All new fields are present in update response!")
                else:
                    print("❌ No 'profile' field in response")        else:
            print(f"❌ PATCH request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def get_access_token():
    """Helper function to get access token - you need to implement this"""
    print("To test the profile endpoint, you need to:")
    print("1. First login using the login endpoint to get an access token")
    print("2. Replace 'YOUR_ACCESS_TOKEN_HERE' in the script with the actual token")
    print("3. Run this script again")
    
    # Example login request (update with actual credentials)
    login_data = {
        "email": "test@example.com",  # Replace with actual email
        "password": "testpassword"    # Replace with actual password
    }
    
    try:
        login_url = f"{BASE_URL}/api/auth/login/"
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Login successful! Access token: {data.get('access_token', 'Not found')}")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    return None

if __name__ == "__main__":
    # First try to get access token
    token = get_access_token()
    
    if token:
        # Update the test function with the actual token
        print(f"\nUse this token in the test function: {token}")
    
    print("\n" + "="*50)
    print("Manual Testing Instructions:")
    print("1. Update the access_token variable in test_profile_endpoint_with_new_fields()")
    print("2. Update login credentials in get_access_token() if needed")
    print("3. Run: test_profile_endpoint_with_new_fields()")
    print("="*50)
