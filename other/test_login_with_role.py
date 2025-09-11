"""
Test script to verify that the login endpoint returns user role
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login/"

def test_login_with_role():
    """Test login endpoint to verify role is returned"""
    
    # Test data - replace with actual test user credentials
    test_credentials = {
        "email": "test@example.com",  # Replace with actual test email
        "password": "testpassword123"  # Replace with actual test password
    }
    
    print("Testing login endpoint with role...")
    print(f"URL: {LOGIN_URL}")
    print(f"Credentials: {test_credentials['email']}")
    
    try:
        # Make login request
        response = requests.post(LOGIN_URL, json=test_credentials)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if role is in response
            if 'user' in data and 'role' in data['user']:
                print(f"✅ User role found: {data['user']['role']}")
            else:
                print("❌ User role not found in response")
                
        else:
            print(f"❌ Login failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_with_role()
