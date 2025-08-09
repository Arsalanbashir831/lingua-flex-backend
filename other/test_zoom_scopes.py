#!/usr/bin/env python3
"""
🔍 Zoom Scopes Diagnosis and Testing Script
This script helps identify the exact scopes needed and tests step by step.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ZoomScopesTester:
    def __init__(self):
        self.account_id = os.getenv('ZOOM_ACCOUNT_ID')
        self.client_id = os.getenv('ZOOM_CLIENT_ID')
        self.client_secret = os.getenv('ZOOM_CLIENT_SECRET')
        self.access_token = None
        
        print("🔍 Zoom Scopes Diagnosis Tool")
        print("=" * 50)
        print(f"Account ID: {self.account_id}")
        print(f"Client ID: {self.client_id[:10]}...")
        print(f"Client Secret: {self.client_secret[:10]}...")
        print()
    
    def get_access_token(self):
        """Get access token with detailed scope information"""
        print("🔑 Step 1: Getting Access Token...")
        
        token_url = "https://zoom.us/oauth/token"
        
        # Token request data
        token_data = {
            'grant_type': 'account_credentials',
            'account_id': self.account_id
        }
        
        # Headers with authentication
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(
                token_url,
                data=token_data,
                headers=headers,
                auth=(self.client_id, self.client_secret)
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                token_info = response.json()
                self.access_token = token_info.get('access_token')
                
                print("✅ Access token obtained!")
                print(f"   Token: {self.access_token[:20]}...")
                print(f"   Type: {token_info.get('token_type', 'N/A')}")
                print(f"   Expires in: {token_info.get('expires_in', 'N/A')} seconds")
                
                # Check if scopes are included in response
                if 'scope' in token_info:
                    print(f"   Granted Scopes: {token_info['scope']}")
                else:
                    print("   ⚠️  No scopes information in token response")
                
                return True
            else:
                print("❌ Failed to get access token")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting access token: {str(e)}")
            return False
    
    def test_endpoint(self, endpoint_name, url, required_scopes=None):
        """Test a specific endpoint and analyze the response"""
        print(f"\n🧪 Step: Testing {endpoint_name}")
        print(f"   URL: {url}")
        if required_scopes:
            print(f"   Required Scopes: {', '.join(required_scopes)}")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {endpoint_name} - SUCCESS!")
                data = response.json()
                
                # Print key information
                if endpoint_name == "User Info":
                    print(f"   User ID: {data.get('id', 'N/A')}")
                    print(f"   Email: {data.get('email', 'N/A')}")
                    print(f"   Type: {data.get('type', 'N/A')}")
                
                return True
                
            elif response.status_code == 400:
                error_data = response.json()
                print(f"❌ {endpoint_name} - FAILED (400 Bad Request)")
                print(f"   Error Code: {error_data.get('code', 'N/A')}")
                print(f"   Message: {error_data.get('message', 'N/A')}")
                
                # Analyze scope-related errors
                if 'scope' in error_data.get('message', '').lower():
                    print("   🔍 SCOPE ISSUE DETECTED!")
                    self.suggest_scopes(error_data.get('message', ''))
                
                return False
                
            else:
                print(f"❌ {endpoint_name} - FAILED ({response.status_code})")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing {endpoint_name}: {str(e)}")
            return False
    
    def suggest_scopes(self, error_message):
        """Analyze error message and suggest correct scopes"""
        print("\n💡 SCOPE ANALYSIS:")
        
        # Parse the scope information from error message
        if "does not contain scopes:" in error_message:
            # Extract the scopes from the error message
            scope_part = error_message.split("does not contain scopes:")[1]
            scope_part = scope_part.strip().rstrip('."]')
            scope_part = scope_part.strip('["]')
            
            print(f"   Raw scope requirement: {scope_part}")
            
            # Parse individual scopes
            if "," in scope_part:
                required_scopes = [s.strip() for s in scope_part.split(",")]
            else:
                required_scopes = [scope_part.strip()]
            
            print("   📋 Required Scopes for Zoom App:")
            for scope in required_scopes:
                # Clean up the scope name
                clean_scope = scope.strip(' "[]')
                print(f"      ✓ {clean_scope}")
            
            print("\n   🔧 ZOOM APP CONFIGURATION:")
            print("   1. Go to https://marketplace.zoom.us/develop/create")
            print("   2. Select your Server-to-Server OAuth app")
            print("   3. Go to 'Scopes' tab")
            print("   4. Add these exact scopes:")
            for scope in required_scopes:
                clean_scope = scope.strip(' "[]')
                print(f"      • {clean_scope}")
            print("   5. Save and wait a few minutes for changes to propagate")
    
    def test_meeting_creation(self):
        """Test meeting creation endpoint"""
        print(f"\n🧪 Step: Testing Meeting Creation")
        
        url = "https://api.zoom.us/v2/users/me/meetings"
        
        meeting_data = {
            "topic": "Test Meeting from LinguaFlex",
            "type": 2,  # Scheduled meeting
            "start_time": "2025-08-06T10:00:00Z",
            "duration": 60,
            "settings": {
                "host_video": True,
                "participant_video": True,
                "waiting_room": False
            }
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, json=meeting_data)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 201:
                print("✅ Meeting Creation - SUCCESS!")
                meeting_info = response.json()
                print(f"   Meeting ID: {meeting_info.get('id')}")
                print(f"   Join URL: {meeting_info.get('join_url')}")
                print(f"   Start URL: {meeting_info.get('start_url')}")
                return meeting_info.get('id')
                
            else:
                print(f"❌ Meeting Creation - FAILED")
                error_data = response.json()
                print(f"   Error: {error_data}")
                
                if 'scope' in str(error_data).lower():
                    self.suggest_scopes(str(error_data))
                
                return None
                
        except Exception as e:
            print(f"❌ Error creating meeting: {str(e)}")
            return None
    
    def run_full_test(self):
        """Run complete scope testing"""
        print("🚀 Starting Full Zoom Scopes Test")
        print("=" * 50)
        
        # Step 1: Get access token
        if not self.get_access_token():
            print("\n❌ Cannot proceed without access token")
            return False
        
        # Step 2: Test user info endpoint
        user_success = self.test_endpoint(
            "User Info", 
            "https://api.zoom.us/v2/users/me",
            ["user:read"]
        )
        
        # Step 3: Test meeting creation if user info works
        if user_success:
            meeting_id = self.test_meeting_creation()
            
            # Step 4: Test meeting deletion if creation worked
            if meeting_id:
                self.test_endpoint(
                    "Meeting Deletion",
                    f"https://api.zoom.us/v2/meetings/{meeting_id}",
                    ["meeting:write"]
                )
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY:")
        print("If you see scope errors above, follow the suggestions to add")
        print("the exact scopes to your Zoom Server-to-Server OAuth app.")
        print("\nAfter adding scopes, wait 2-3 minutes and run this test again.")

if __name__ == "__main__":
    tester = ZoomScopesTester()
    tester.run_full_test()
