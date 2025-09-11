"""
Test script to verify that the profile picture upload endpoint returns proper Supabase URLs
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PROFILE_PICTURE_UPLOAD_URL = f"{BASE_URL}/user/profile-picture/"
PROFILE_PICTURE_GET_URL = f"{BASE_URL}/user/profile-picture/get/"

def test_profile_picture_endpoints():
    """Test profile picture upload and get endpoints"""
    
    # You'll need to provide a valid access token for testing
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("Testing profile picture endpoints...")
    print(f"Upload URL: {PROFILE_PICTURE_UPLOAD_URL}")
    print(f"Get URL: {PROFILE_PICTURE_GET_URL}")
    
    try:
        # Test GET request to check current profile picture
        print("\n=== Testing GET Profile Picture ===")
        response = requests.get(PROFILE_PICTURE_GET_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ GET request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if URL is a proper Supabase URL
            profile_url = data.get('profile_picture_url')
            if profile_url and 'supabase' in profile_url and '/storage/v1/object/public/' in profile_url:
                print("✅ Profile picture URL is a valid Supabase URL!")
            else:
                print("❌ Profile picture URL is not a valid Supabase URL")
                
        elif response.status_code == 404:
            print("ℹ️ No profile picture found (this is normal if none uploaded yet)")
        else:
            print(f"❌ GET request failed: {response.text}")
        
        # Test POST request (upload)
        print("\n=== Testing POST Profile Picture Upload ===")
        print("Note: You need to manually test the upload with a real image file")
        print("Expected behavior after upload:")
        print("- The response should contain a proper Supabase URL")
        print("- URL format: https://your-project.supabase.co/storage/v1/object/public/user-uploads/user_id/filename")
        
        # Instructions for manual testing
        print("\n=== Manual Upload Test Instructions ===")
        print("1. Use Postman or similar tool")
        print("2. POST to:", PROFILE_PICTURE_UPLOAD_URL)
        print("3. Headers: Authorization: Bearer {your_token}")
        print("4. Body: form-data with key 'profile_picture' and select an image file")
        print("5. Check that response includes proper Supabase URL in profile_picture field")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def get_access_token():
    """Helper function to get access token"""
    print("To test the profile picture endpoints, you need to:")
    print("1. First login using the login endpoint to get an access token")
    print("2. Replace 'YOUR_ACCESS_TOKEN_HERE' in the script with the actual token")
    print("3. Run this script again")
    
    # Example login request
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
    print("=== Profile Picture Endpoint Testing ===")
    
    # First try to get access token
    token = get_access_token()
    
    if token:
        print(f"\nUse this token in the test function: {token}")
    
    print("\n" + "="*60)
    print("Manual Testing Instructions:")
    print("1. Update the access_token variable in test_profile_picture_endpoints()")
    print("2. Update login credentials in get_access_token() if needed")
    print("3. Run: test_profile_picture_endpoints()")
    print("="*60)
    
    # Uncomment this line after setting the correct token
    # test_profile_picture_endpoints()
