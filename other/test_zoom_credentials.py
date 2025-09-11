#!/usr/bin/env python3
"""
Quick test to verify Zoom API credentials are working
Run this before testing in Postman
"""

import jwt
import time
import requests
import os
from pathlib import Path

# Load environment variables
def load_env():
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def test_zoom_credentials():
    """Test if Zoom API credentials are working"""
    
    load_env()
    
    # Get credentials from environment
    api_key ="8t0mzl52ScOdw319JY_isw"
    api_secret ="kvaJgTuZJVJruqSnY7vzecOF7t3XFiZc"
    account_id ="ZJmI_gxfSoqVY84zdfzaEA"
    
    print("🔍 Testing Zoom API Credentials...")
    print("=" * 50)
    
    # Check if credentials exist
    if not api_key or not api_secret:
        print("❌ Missing Zoom credentials in .env file")
        print("Required: ZOOM_API_KEY, ZOOM_API_SECRET")
        return False
    
    print(f"✅ API Key: {api_key[:10]}...")
    print(f"✅ API Secret: {api_secret[:10]}...")
    print(f"✅ Account ID: {account_id}")
    
    # Generate JWT token
    try:
        payload = {
            'iss': api_key,
            'exp': int(time.time() + 3600)  # 1 hour expiry
        }
        
        token = jwt.encode(payload, api_secret, algorithm='HS256')
        print("✅ JWT token generated successfully")
        
    except Exception as e:
        print(f"❌ JWT token generation failed: {str(e)}")
        return False
    
    # Test API connectivity
    print("\n🌐 Testing Zoom API connectivity...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test basic API call
        response = requests.get('https://api.zoom.us/v2/users/me', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Zoom API connection successful!")
            print(f"   User: {user_data.get('email', 'Unknown')}")
            print(f"   Type: {user_data.get('type', 'Unknown')}")
            print(f"   Account: {user_data.get('account_id', 'Unknown')}")
            
            # Check if user can create meetings
            user_type = user_data.get('type', 1)
            if user_type >= 2:  # Pro or higher
                print("✅ Account can create meetings via API")
            else:
                print("⚠️  Basic account - may not create meetings via API")
                
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication failed - Invalid API key/secret")
            print(f"   Response: {response.text}")
            return False
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_meeting_creation():
    """Test creating a sample meeting"""
    
    load_env()
    
    api_key = os.getenv('ZOOM_API_KEY', '')
    api_secret = os.getenv('ZOOM_API_SECRET', '')
    
    if not api_key or not api_secret:
        print("❌ Missing credentials for meeting test")
        return False
    
    print("\n📹 Testing meeting creation...")
    
    # Generate token
    payload = {
        'iss': api_key,
        'exp': int(time.time() + 3600)
    }
    token = jwt.encode(payload, api_secret, algorithm='HS256')
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test meeting data
    meeting_data = {
        'topic': 'LinguaFlex Test Meeting',
        'type': 2,  # Scheduled meeting
        'start_time': '2025-08-06T10:00:00Z',
        'duration': 60,
        'timezone': 'UTC',
        'settings': {
            'host_video': True,
            'participant_video': True,
            'join_before_host': True,
            'mute_upon_entry': True,
            'approval_type': 0,
            'audio': 'both'
        }
    }
    
    try:
        # First get user info to use their email
        user_response = requests.get('https://api.zoom.us/v2/users/me', headers=headers)
        
        if user_response.status_code != 200:
            print("❌ Cannot get user info for meeting test")
            return False
        
        user_email = user_response.json().get('email')
        
        # Create meeting
        meeting_url = f'https://api.zoom.us/v2/users/{user_email}/meetings'
        response = requests.post(meeting_url, json=meeting_data, headers=headers)
        
        if response.status_code == 201:
            meeting_info = response.json()
            meeting_id = meeting_info.get('id')
            join_url = meeting_info.get('join_url')
            
            print("✅ Test meeting created successfully!")
            print(f"   Meeting ID: {meeting_id}")
            print(f"   Join URL: {join_url}")
            
            # Clean up - delete the test meeting
            delete_response = requests.delete(f'https://api.zoom.us/v2/meetings/{meeting_id}', headers=headers)
            if delete_response.status_code == 204:
                print("✅ Test meeting deleted successfully")
            
            return True
            
        else:
            print(f"❌ Meeting creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Meeting test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    
    print("🧪 Zoom API Credential Test Suite")
    print("=" * 50)
    
    # Test 1: Credentials and connectivity
    if not test_zoom_credentials():
        print("\n❌ Credential test failed - check your .env file")
        return
    
    # Test 2: Meeting creation
    if not test_meeting_creation():
        print("\n⚠️  Meeting creation test failed - but basic auth works")
        print("   This might be due to account permissions")
    
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    print("✅ Zoom credentials are configured and working")
    print("✅ API connectivity established")
    print("✅ Ready for Postman testing!")
    print("\nNext steps:")
    print("1. Open Postman")
    print("2. Import LinguaFlex_Zoom_API.postman_collection.json")
    print("3. Test booking creation with Zoom integration")

if __name__ == "__main__":
    main()
