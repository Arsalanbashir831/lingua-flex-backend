#!/usr/bin/env python3
"""
Test script for Campaign Specific Student Targeting API
Tests the new functionality to send campaigns to selected students
"""

import requests
import json
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

def test_get_available_students():
    """Test getting list of available students"""
    print("\n👥 Testing Get Available Students...")
    
    response = requests.get(f"{BASE_URL}/campaigns/teacher/students/", headers=HEADERS)
    print_response(response, "Get Available Students")
    
    if response.status_code == 200:
        students_data = response.json()
        print(f"✅ Found {students_data.get('count', 0)} students")
        
        # Return first few student emails for testing
        students = students_data.get('students', [])
        if students:
            return [student['email'] for student in students[:3]]  # Return first 3 emails
        else:
            print("⚠️ No students found in the system")
            return []
    else:
        print(f"❌ Failed to get students list")
        return []

def test_create_campaign_for_targeting():
    """Create a campaign specifically for targeting tests"""
    print("\n📝 Creating Campaign for Targeting Tests...")
    
    campaign_data = {
        "title": f"Targeted Campaign Test {datetime.now().strftime('%H:%M:%S')}",
        "subject": "🎯 Personalized Learning Opportunity",
        "content": """Hello {{student_name}},

I hope you're doing well in your language learning journey! I wanted to reach out personally with a special opportunity that might interest you.

🌟 **Personalized Learning Session**
Based on your learning profile, I believe you would benefit from:
- One-on-one conversation practice
- Customized grammar exercises
- Cultural context lessons
- Pronunciation improvement techniques

📅 **Special Offer for Selected Students**
I'm offering a complimentary 30-minute consultation to discuss your specific learning goals and create a personalized study plan.

This is a limited opportunity available only to select students who have shown dedication to their language learning.

Would you be interested in scheduling this session? Simply reply to this email with your preferred time slots.

Looking forward to helping you achieve your language goals!

Best regards,
Your Language Teacher""",
        "from_name": "Language Teacher",
        "from_email": "teacher@linguaflex.com",
        "notes": "Targeted campaign test for specific student selection"
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/", json=campaign_data, headers=HEADERS)
    print_response(response, "Create Targeted Campaign")
    
    if response.status_code == 201:
        campaign_id = response.json().get('id')
        print(f"✅ Campaign created successfully with ID: {campaign_id}")
        return campaign_id
    else:
        print(f"❌ Failed to create campaign")
        return None

def test_send_to_specific_students(campaign_id, student_emails):
    """Test sending campaign to specific students"""
    print(f"\n📧 Testing Send to Specific Students (Campaign ID: {campaign_id})...")
    
    if not student_emails:
        print("❌ No student emails available for testing")
        return
    
    print(f"🎯 Targeting {len(student_emails)} students: {', '.join(student_emails)}")
    
    # WARNING: This will actually send emails if RESEND_API_KEY is configured!
    print("⚠️  WARNING: This will send real emails to the specified students!")
    user_input = input("Do you want to proceed? (yes/no): ").lower().strip()
    
    if user_input != 'yes':
        print("❌ Targeted campaign sending test skipped by user")
        return
    
    send_data = {
        "confirm_send": True,
        "student_emails": student_emails
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Send to Specific Students")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Campaign sent successfully!")
        print(f"   📊 Sent: {result.get('sent_count', 0)}")
        print(f"   📊 Failed: {result.get('failed_count', 0)}")
        print(f"   📊 Total Recipients: {result.get('total_recipients', 0)}")
        print(f"   📊 Requested Emails: {result.get('requested_emails', 0)}")
        
        if result.get('missing_students'):
            print(f"   ⚠️ Missing Students: {', '.join(result['missing_students'])}")
        
        return result
    else:
        print(f"❌ Failed to send targeted campaign")
        return None

def test_send_with_invalid_emails(campaign_id):
    """Test sending with invalid/non-existent student emails"""
    print(f"\n🔍 Testing Send with Invalid Emails (Campaign ID: {campaign_id})...")
    
    invalid_emails = [
        "nonexistent1@example.com",
        "invalid2@test.com",
        "fake3@dummy.org"
    ]
    
    send_data = {
        "confirm_send": True,
        "student_emails": invalid_emails
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Send with Invalid Emails")
    
    if response.status_code == 500:  # Should fail because no valid students found
        print(f"✅ Correctly handled invalid emails")
    else:
        print(f"⚠️ Unexpected response for invalid emails")

def test_send_validation_errors(campaign_id):
    """Test validation errors for specific student sending"""
    print(f"\n❌ Testing Validation Errors...")
    
    # Test 1: Empty student emails list
    send_data = {
        "confirm_send": True,
        "student_emails": []
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Empty Student Emails List")
    
    # Test 2: Invalid email format
    send_data = {
        "confirm_send": True,
        "student_emails": ["invalid-email", "another@invalid"]
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Invalid Email Format")
    
    # Test 3: Missing confirm_send
    send_data = {
        "student_emails": ["test@example.com"]
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Missing Confirm Send")
    
    # Test 4: confirm_send = false
    send_data = {
        "confirm_send": False,
        "student_emails": ["test@example.com"]
    }
    
    response = requests.post(f"{BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/", json=send_data, headers=HEADERS)
    print_response(response, "Confirm Send False")

def test_comparison_endpoints(campaign_id, student_emails):
    """Compare the original send-all vs send-to-specific endpoints"""
    print(f"\n🔄 Testing Endpoint Comparison...")
    
    # Test original send endpoint (send to all)
    print("🌍 Original Send to All Students endpoint:")
    print(f"   URL: {BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send/")
    print("   Behavior: Sends to ALL students in the system")
    
    # Test new send to specific endpoint
    print("🎯 New Send to Specific Students endpoint:")
    print(f"   URL: {BASE_URL}/campaigns/teacher/campaigns/{campaign_id}/send-to-students/")
    print(f"   Behavior: Sends to {len(student_emails)} specific students")
    print(f"   Target Emails: {', '.join(student_emails)}")

def run_targeted_campaign_tests():
    """Run all targeted campaign tests"""
    print("🎯 Starting Targeted Campaign API Tests")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Base URL: {BASE_URL}")
    
    # Check if token is configured
    if TEACHER_TOKEN == "your_teacher_token_here":
        print("\n❌ Error: Please configure TEACHER_TOKEN in the script")
        print("   1. Get a teacher token by logging in through the API")
        print("   2. Replace 'your_teacher_token_here' with the actual token")
        return
    
    try:
        # Test 1: Get available students
        student_emails = test_get_available_students()
        
        if not student_emails:
            print("\n❌ Cannot continue tests without student emails")
            print("   Make sure there are students in the system with role='STUDENT'")
            return
        
        # Test 2: Create a campaign for targeting
        campaign_id = test_create_campaign_for_targeting()
        
        if campaign_id:
            # Test 3: Compare endpoints
            test_comparison_endpoints(campaign_id, student_emails)
            
            # Test 4: Validation errors
            test_send_validation_errors(campaign_id)
            
            # Test 5: Send with invalid emails
            test_send_with_invalid_emails(campaign_id)
            
            # Test 6: Send to specific students (optional - requires confirmation)
            # test_send_to_specific_students(campaign_id, student_emails)
            
            print(f"\n🚫 Actual email sending test skipped (uncomment in script to test)")
            print(f"   To test email sending, uncomment the line above and run again")
        
        print(f"\n🎉 Targeted Campaign API Testing Complete!")
        print(f"📝 New Features Available:")
        print(f"   ✅ Get list of available students")
        print(f"   ✅ Send campaigns to specific students")
        print(f"   ✅ Validate student emails")
        print(f"   ✅ Track missing/invalid students")
        print(f"   ✅ Detailed sending results")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Cannot connect to {BASE_URL}")
        print("   Make sure the Django development server is running")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")

if __name__ == "__main__":
    # Configuration check
    print("🔧 Targeted Campaign API Test Configuration:")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Token configured: {'Yes' if TEACHER_TOKEN != 'your_teacher_token_here' else 'No'}")
    print(f"   Test mode: Targeted Student Selection")
    
    run_targeted_campaign_tests()
