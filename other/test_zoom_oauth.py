#!/usr/bin/env python3
"""
Test script for latest Zoom Server-to-Server OAuth implementation
Based on Zoom's current API documentation (2024-2025)
"""

import requests
import base64
import time
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Load environment variables
def load_env():
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def get_zoom_access_token():
    """Get access token using Server-to-Server OAuth (latest method)"""
    
    load_env()
    
    account_id = os.getenv('ZOOM_ACCOUNT_ID', '')
    client_id = os.getenv('ZOOM_CLIENT_ID', '')
    client_secret = os.getenv('ZOOM_CLIENT_SECRET', '')
    
    if not all([account_id, client_id, client_secret]):
        print("❌ Missing Zoom credentials")
        return None
    
    print(f"🔑 Testing Server-to-Server OAuth...")
    print(f"   Account ID: {account_id}")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Client Secret: {client_secret[:10]}...")
    
    # Encode credentials for Basic Auth
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Token request
    token_url = 'https://zoom.us/oauth/token'
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'account_credentials',
        'account_id': account_id
    }
    
    try:
        print("🌐 Requesting access token...")
        response = requests.post(token_url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            
            print("✅ Access token obtained successfully!")
            print(f"   Token: {access_token[:20]}...")
            print(f"   Expires in: {expires_in} seconds")
            
            return access_token
        else:
            print(f"❌ Token request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting token: {str(e)}")
        return None

def test_user_info(access_token):
    """Test getting user information"""
    
    print("\n👤 Testing user info endpoint...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.zoom.us/v2/users/me', headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ User info retrieved successfully!")
            print(f"   Email: {user_data.get('email', 'Unknown')}")
            print(f"   Display Name: {user_data.get('display_name', 'Unknown')}")
            print(f"   Account ID: {user_data.get('account_id', 'Unknown')}")
            print(f"   User Type: {user_data.get('type', 'Unknown')} (1=Basic, 2=Pro, 3=Corp)")
            
            # Check if user can create meetings
            user_type = user_data.get('type', 1)
            if user_type >= 2:
                print("✅ Account can create meetings via API")
            else:
                print("⚠️  Basic account - may not create meetings via API")
                
            return user_data
        else:
            print(f"❌ User info failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting user info: {str(e)}")
        return None

def test_create_meeting(access_token, user_email):
    """Test creating a meeting"""
    
    print("\n📹 Testing meeting creation...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Meeting data based on latest API specs
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    meeting_data = {
        'topic': 'LinguaFlex API Test Meeting',
        'type': 2,  # Scheduled meeting
        'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'duration': 60,
        'timezone': 'UTC',
        'agenda': 'Test meeting created by LinguaFlex booking system',
        'settings': {
            'host_video': True,
            'participant_video': True,
            'join_before_host': True,
            'mute_upon_entry': False,
            'watermark': False,
            'use_pmi': False,
            'approval_type': 0,  # Automatically approve
            'audio': 'both',
            'auto_recording': 'none',
            'waiting_room': False,
            'meeting_authentication': False,
            'encryption_type': 'enhanced_encryption'
        }
    }
    
    url = f'https://api.zoom.us/v2/users/{user_email}/meetings'
    
    try:
        response = requests.post(url, json=meeting_data, headers=headers, timeout=30)
        
        if response.status_code == 201:
            meeting_info = response.json()
            meeting_id = meeting_info.get('id')
            join_url = meeting_info.get('join_url')
            start_url = meeting_info.get('start_url')
            password = meeting_info.get('password', '')
            
            print("✅ Meeting created successfully!")
            print(f"   Meeting ID: {meeting_id}")
            print(f"   Join URL: {join_url}")
            print(f"   Start URL: {start_url}")
            if password:
                print(f"   Password: {password}")
            
            return meeting_id
        else:
            print(f"❌ Meeting creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating meeting: {str(e)}")
        return None

def test_delete_meeting(access_token, meeting_id):
    """Test deleting a meeting"""
    
    if not meeting_id:
        return
        
    print(f"\n🗑️  Testing meeting deletion for ID: {meeting_id}...")
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    url = f'https://api.zoom.us/v2/meetings/{meeting_id}'
    
    try:
        response = requests.delete(url, headers=headers, timeout=10)
        
        if response.status_code == 204:
            print("✅ Meeting deleted successfully!")
        else:
            print(f"⚠️  Delete response: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error deleting meeting: {str(e)}")

def main():
    """Run comprehensive Zoom API test"""
    
    print("🧪 Zoom Server-to-Server OAuth API Test")
    print("Using Latest Zoom API Documentation (2024-2025)")
    print("=" * 60)
    
    # Step 1: Get access token
    access_token = get_zoom_access_token()
    if not access_token:
        print("\n❌ Cannot proceed without access token")
        return
    
    # Step 2: Test user info
    user_data = test_user_info(access_token)
    if not user_data:
        print("\n❌ Cannot proceed without user info")
        return
    
    user_email = user_data.get('email')
    if not user_email:
        print("\n❌ No user email found")
        return
    
    # Step 3: Test meeting creation
    meeting_id = test_create_meeting(access_token, user_email)
    
    # Step 4: Clean up (delete test meeting)
    if meeting_id:
        test_delete_meeting(access_token, meeting_id)
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    
    if access_token and user_data and meeting_id:
        print("✅ All tests passed!")
        print("✅ Zoom Server-to-Server OAuth working correctly")
        print("✅ Meeting creation/deletion working")
        print("✅ Ready for LinguaFlex booking integration!")
    else:
        print("⚠️  Some tests failed - check credentials and account type")
    
    print("\n📋 Next Steps:")
    print("1. ✅ Zoom credentials are working")
    print("2. 🔄 Restart Django server")
    print("3. 📱 Test in Postman")
    print("4. 🎯 Create actual bookings with Zoom meetings")

if __name__ == "__main__":
    main()
