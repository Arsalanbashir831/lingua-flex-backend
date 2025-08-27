#!/usr/bin/env python3
"""
Comprehensive test script for Campaign Management API endpoints
Tests all campaign functionality including creation, sending, and management
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"  # Adjust as needed
TEACHER_TOKEN = "your_teacher_token_here"  # Replace with actual teacher token

# Headers
HEADERS = {
    "Authorization": f"Bearer {TEACHER_TOKEN}",
    "Content-Type": "application/json"
}

def print_response(response, title):
    """Helper function to print formatted responses"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2)}")
    except:
        print(f"Response Text: {response.text}")
    
    print(f"{'='*60}")

def test_campaign_creation():
    """Test creating a new campaign"""
    print("\n🚀 Testing Campaign Creation...")
    
    campaign_data = {
        "title": "Summer Language Learning Special",
        "subject": "🌟 Unlock Your Language Potential This Summer!",
        "content": """Hello {{student_name}},

I hope this message finds you well! As we approach the summer season, I wanted to reach out with an exciting opportunity to accelerate your language learning journey.

🎯 **What I'm Offering:**
- Personalized one-on-one language sessions
- Flexible scheduling to fit your summer plans  
- Interactive conversation practice
- Cultural immersion experiences
- Customized learning materials

📚 **Special Summer Package:**
- 10 sessions for the price of 8
- Free initial assessment and learning plan
- Access to exclusive learning resources
- Progress tracking and regular feedback

Whether you're preparing for travel, academic requirements, or personal enrichment, I'm here to help you achieve your language goals efficiently and enjoyably.

🗓️ **Limited Time Offer:**
Book your sessions before the end of August and receive a 20% discount on my regular rates!

Feel free to reply to this email or book a consultation through the LinguaFlex platform. I'd love to discuss how we can tailor the perfect learning experience for you.

Looking forward to our language learning adventure together!

Best regards,
[Your Language Teacher]""",
        "from_name": "Sarah Johnson",
        "from_email": "sarah.teacher@linguaflex.com",
        "notes": "Summer 2025 promotional campaign targeting all students"
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/", json=campaign_data, headers=HEADERS)
    print_response(response, "Create Campaign")
    
    if response.status_code == 201:
        campaign_id = response.json().get('id')
        print(f"✅ Campaign created successfully with ID: {campaign_id}")
        return campaign_id
    else:
        print(f"❌ Failed to create campaign")
        return None

def test_campaign_list():
    """Test listing campaigns"""
    print("\n📋 Testing Campaign List...")
    
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/", headers=HEADERS)
    print_response(response, "List Campaigns")
    
    if response.status_code == 200:
        campaigns = response.json().get('results', [])
        print(f"✅ Found {len(campaigns)} campaigns")
        return campaigns
    else:
        print(f"❌ Failed to list campaigns")
        return []

def test_campaign_detail(campaign_id):
    """Test getting campaign details"""
    print(f"\n🔍 Testing Campaign Detail (ID: {campaign_id})...")
    
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/", headers=HEADERS)
    print_response(response, "Campaign Detail")
    
    if response.status_code == 200:
        print(f"✅ Campaign details retrieved successfully")
        return response.json()
    else:
        print(f"❌ Failed to get campaign details")
        return None

def test_campaign_preview(campaign_id):
    """Test campaign email preview"""
    print(f"\n👀 Testing Campaign Preview (ID: {campaign_id})...")
    
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/preview/", headers=HEADERS)
    print_response(response, "Campaign Preview")
    
    if response.status_code == 200:
        print(f"✅ Campaign preview generated successfully")
        return response.json()
    else:
        print(f"❌ Failed to generate campaign preview")
        return None

def test_campaign_update(campaign_id):
    """Test updating a campaign"""
    print(f"\n✏️ Testing Campaign Update (ID: {campaign_id})...")
    
    update_data = {
        "title": "Updated Summer Language Learning Special",
        "notes": "Updated campaign with better messaging"
    }
    
    response = requests.patch(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/", json=update_data, headers=HEADERS)
    print_response(response, "Update Campaign")
    
    if response.status_code == 200:
        print(f"✅ Campaign updated successfully")
        return response.json()
    else:
        print(f"❌ Failed to update campaign")
        return None

def test_campaign_stats():
    """Test campaign statistics"""
    print("\n📊 Testing Campaign Statistics...")
    
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/stats/", headers=HEADERS)
    print_response(response, "Campaign Statistics")
    
    if response.status_code == 200:
        print(f"✅ Campaign statistics retrieved successfully")
        return response.json()
    else:
        print(f"❌ Failed to get campaign statistics")
        return None

def test_campaign_send(campaign_id):
    """Test sending a campaign"""
    print(f"\n📧 Testing Campaign Send (ID: {campaign_id})...")
    
    # WARNING: This will actually send emails if RESEND_API_KEY is configured!
    print("⚠️  WARNING: This will send real emails to all students!")
    user_input = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if user_input != 'yes':
        print("❌ Campaign sending test skipped by user")
        return None
    
    send_data = {
        "confirm_send": True
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send/", json=send_data, headers=HEADERS)
    print_response(response, "Send Campaign")
    
    if response.status_code == 200:
        print(f"✅ Campaign sent successfully")
        return response.json()
    else:
        print(f"❌ Failed to send campaign")
        return None

def test_search_and_filter():
    """Test campaign search and filtering"""
    print("\n🔎 Testing Campaign Search and Filtering...")
    
    # Test search
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/?search=summer", headers=HEADERS)
    print_response(response, "Search Campaigns (summer)")
    
    # Test status filter
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/?status=draft", headers=HEADERS)
    print_response(response, "Filter Campaigns (draft)")
    
    if response.status_code == 200:
        print(f"✅ Search and filtering working correctly")
    else:
        print(f"❌ Search and filtering failed")

def test_error_scenarios():
    """Test various error scenarios"""
    print("\n❌ Testing Error Scenarios...")
    
    # Test with invalid campaign ID
    response = requests.get(f"{BASE_URL}/campaigns/teacher/campaigns/99999/", headers=HEADERS)
    print_response(response, "Invalid Campaign ID")
    
    # Test sending campaign with invalid confirmation
    send_data = {"confirm_send": False}
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/1/send/", json=send_data, headers=HEADERS)
    print_response(response, "Invalid Send Confirmation")
    
    # Test creating campaign with missing data
    invalid_data = {"title": ""}
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/", json=invalid_data, headers=HEADERS)
    print_response(response, "Invalid Campaign Data")

def run_comprehensive_test():
    """Run all campaign tests"""
    print("🎯 Starting Comprehensive Campaign API Tests")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Base URL: {BASE_URL}")
    
    # Check if token is configured
    if TEACHER_TOKEN == "your_teacher_token_here":
        print("\n❌ Error: Please configure TEACHER_TOKEN in the script")
        print("   1. Get a teacher token by logging in through the API")
        print("   2. Replace 'your_teacher_token_here' with the actual token")
        return
    
    try:
        # Test 1: Create a campaign
        campaign_id = test_campaign_creation()
        
        if campaign_id:
            # Test 2: List campaigns
            campaigns = test_campaign_list()
            
            # Test 3: Get campaign details
            test_campaign_detail(campaign_id)
            
            # Test 4: Preview campaign
            test_campaign_preview(campaign_id)
            
            # Test 5: Update campaign
            test_campaign_update(campaign_id)
            
            # Test 6: Get campaign statistics
            test_campaign_stats()
            
            # Test 7: Search and filter
            test_search_and_filter()
            
            # Test 8: Send campaign (optional - requires confirmation)
            # test_campaign_send(campaign_id)
            
            print(f"\n🚫 Campaign sending test skipped (uncomment in script to test)")
        
        # Test 9: Error scenarios
        test_error_scenarios()
        
        print(f"\n🎉 Campaign API Testing Complete!")
        print(f"📝 Review the results above to ensure all endpoints are working correctly")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Cannot connect to {BASE_URL}")
        print("   Make sure the Django development server is running")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")

if __name__ == "__main__":
    # Configuration check
    print("🔧 Campaign API Test Configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Token configured: {'Yes' if TEACHER_TOKEN != 'your_teacher_token_here' else 'No'}")
    print(f"   Test mode: Comprehensive")
    
    run_comprehensive_test()
