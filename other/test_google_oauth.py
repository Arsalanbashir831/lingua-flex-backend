#!/usr/bin/env python3
"""
Test script for Google OAuth authentication system
"""

import requests
import json
import os
import sys

# Add the Django project to the Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')

def test_oauth_initiate():
    """Test Step 1: Initiate Google OAuth flow"""
    url = "http://127.0.0.1:8000/api/auth/google/initiate/"
    
    data = {
        "role": "STUDENT",
        "redirect_url": "http://localhost:3000/auth/callback"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"🚀 Step 1: Initiate Google OAuth")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ OAuth URL generated: {result.get('oauth_url')[:100]}...")
            return result.get('oauth_url')
        else:
            print(f"❌ Failed to initiate OAuth")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_oauth_callback():
    """Test Step 2: Handle OAuth callback (simulation)"""
    url = "http://127.0.0.1:8000/api/auth/google/callback/"
    
    # This would normally be provided by Supabase after OAuth
    # For testing, you would need real tokens from Supabase OAuth flow
    data = {
        "access_token": "MOCK_ACCESS_TOKEN",  # Replace with real token
        "refresh_token": "MOCK_REFRESH_TOKEN",  # Replace with real token
        "role": "STUDENT"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"\n🔐 Step 2: Handle OAuth Callback")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User authenticated: {result.get('user', {}).get('email')}")
            return result.get('access_token')
        else:
            print(f"❌ OAuth callback failed")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_oauth_status(access_token):
    """Test Step 3: Check OAuth status"""
    url = "http://127.0.0.1:8000/api/auth/google/status/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n📊 Step 3: Check OAuth Status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Profile complete: {result.get('profile_complete')}")
            return result.get('profile_complete')
        else:
            print(f"❌ Status check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_complete_profile(access_token):
    """Test Step 4: Complete OAuth user profile"""
    url = "http://127.0.0.1:8000/api/auth/google/complete-profile/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Student profile data
    data = {
        "proficiency_level": "INTERMEDIATE",
        "learning_goals": "I want to improve my conversational English skills",
        "target_languages": ["English", "Spanish"],
        "phone_number": "+1234567890"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\n✏️ Step 4: Complete Profile")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Profile completed for: {result.get('user', {}).get('email')}")
            return True
        else:
            print(f"❌ Profile completion failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 Testing Google OAuth Authentication System")
    print("=" * 60)
    
    # Test 1: Initiate OAuth flow
    oauth_url = test_oauth_initiate()
    if not oauth_url:
        print("❌ Cannot proceed without OAuth URL")
        return
    
    # Test 2: OAuth callback (requires manual intervention)
    print(f"\n⚠️  Manual Step Required:")
    print(f"1. Open this URL in browser: {oauth_url}")
    print(f"2. Complete Google OAuth flow")
    print(f"3. Get access_token from Supabase")
    print(f"4. Update test_oauth_callback() with real tokens")
    print(f"5. Uncomment and run remaining tests")
    
    # Note: The following tests require real OAuth tokens
    # Uncomment and update tokens after completing OAuth flow
    
    # access_token = test_oauth_callback()
    # if access_token:
    #     profile_complete = test_oauth_status(access_token)
    #     if not profile_complete:
    #         test_complete_profile(access_token)
    #         test_oauth_status(access_token)  # Check again
    
    print(f"\n✅ OAuth system setup complete!")
    print(f"📖 See GOOGLE_OAUTH_SETUP_GUIDE.md for detailed setup instructions")

if __name__ == "__main__":
    main()
