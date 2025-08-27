#!/usr/bin/env python3
"""
Quick test of the targeted campaign endpoint to see debug output
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
CAMPAIGN_ID = 6  # Use the campaign ID from the user's test
STUDENT_EMAIL = "hacib31593@evoxury.com"

# Note: You'll need to replace this with a valid teacher token
# Get it by logging in through the API first
TEACHER_TOKEN = "your_teacher_token_here"

def test_targeted_sending():
    """Test the targeted sending endpoint"""
    print("🔧 Testing Targeted Campaign Sending with Debug Output")
    print("=" * 60)
    
    if TEACHER_TOKEN == "your_teacher_token_here":
        print("❌ Please configure TEACHER_TOKEN in the script")
        return
    
    url = f"{BASE_URL}/campaigns/teacher/campaigns/{CAMPAIGN_ID}/send-to-students/"
    
    headers = {
        "Authorization": f"Bearer {TEACHER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "confirm_send": True,
        "student_emails": [STUDENT_EMAIL]
    }
    
    print(f"📞 Making request to: {url}")
    print(f"📧 Sending to: {STUDENT_EMAIL}")
    print(f"📋 Campaign ID: {CAMPAIGN_ID}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Request successful!")
            print(f"   Sent count: {result.get('sent_count')}")
            print(f"   Failed count: {result.get('failed_count')}")
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error making request: {e}")

if __name__ == "__main__":
    print("⚠️  Note: This script requires a valid teacher token.")
    print("⚠️  Run the Django server and check the logs for debug output.")
    print("⚠️  The actual debug information will appear in the Django console.")
    print()
    test_targeted_sending()
