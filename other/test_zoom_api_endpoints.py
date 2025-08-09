#!/usr/bin/env python3
"""
Quick test script for Zoom Meeting API endpoints
Run this to verify all endpoints are working before using Postman
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials (replace with your actual test accounts)
TEACHER_CREDENTIALS = {
    "email": "teacher@example.com",
    "password": "your_password"
}

STUDENT_CREDENTIALS = {
    "email": "student@example.com", 
    "password": "your_password"
}

class ZoomAPITester:
    def __init__(self):
        self.teacher_token = None
        self.student_token = None
        self.teacher_id = None
        self.student_id = None
        self.booking_id = None
        
    def login(self, credentials, user_type):
        """Login and get authentication token"""
        url = f"{API_BASE}/login/"
        response = requests.post(url, json=credentials)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user_id = data.get('user', {}).get('id')
            
            if user_type == 'teacher':
                self.teacher_token = token
                self.teacher_id = user_id
            else:
                self.student_token = token
                self.student_id = user_id
                
            print(f"✅ {user_type.capitalize()} login successful")
            return True
        else:
            print(f"❌ {user_type.capitalize()} login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def get_headers(self, user_type='teacher'):
        """Get authorization headers"""
        token = self.teacher_token if user_type == 'teacher' else self.student_token
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def test_endpoints(self):
        """Test all Zoom booking endpoints"""
        print("🚀 Starting Zoom Meeting API Tests...")
        print("=" * 50)
        
        # Step 1: Login as teacher and student
        if not self.login(TEACHER_CREDENTIALS, 'teacher'):
            return False
        if not self.login(STUDENT_CREDENTIALS, 'student'):
            return False
            
        # Step 2: Test teacher availability creation
        self.test_create_availability()
        
        # Step 3: Test available slots retrieval
        self.test_get_available_slots()
        
        # Step 4: Test booking creation (with Zoom meeting)
        self.test_create_booking()
        
        # Step 5: Test booking details retrieval
        if self.booking_id:
            self.test_get_booking_details()
            
        # Step 6: Test booking reschedule (updates Zoom meeting)
        if self.booking_id:
            self.test_reschedule_booking()
            
        # Step 7: Test my bookings
        self.test_get_my_bookings()
        
        print("=" * 50)
        print("✅ All tests completed!")
        
    def test_create_availability(self):
        """Test creating teacher availability"""
        url = f"{API_BASE}/bookings/availability/"
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = {
            "date": tomorrow,
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "is_available": True
        }
        
        response = requests.post(url, json=data, headers=self.get_headers('teacher'))
        
        if response.status_code in [200, 201]:
            print("✅ Teacher availability created successfully")
        else:
            print(f"⚠️  Teacher availability creation: {response.status_code}")
            print(f"Response: {response.text}")
    
    def test_get_available_slots(self):
        """Test getting available slots"""
        url = f"{API_BASE}/bookings/slots/available/"
        
        response = requests.get(url, headers=self.get_headers('student'))
        
        if response.status_code == 200:
            slots = response.json()
            print(f"✅ Available slots retrieved: {len(slots)} slots found")
        else:
            print(f"⚠️  Get available slots: {response.status_code}")
            print(f"Response: {response.text}")
    
    def test_create_booking(self):
        """Test creating a session booking (should create Zoom meeting)"""
        url = f"{API_BASE}/bookings/bookings/"
        tomorrow = datetime.now() + timedelta(days=1)
        start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        data = {
            "teacher": self.teacher_id,
            "start_time": start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "end_time": end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "session_type": "video_call",
            "notes": "Test session for Zoom integration"
        }
        
        response = requests.post(url, json=data, headers=self.get_headers('student'))
        
        if response.status_code in [200, 201]:
            booking_data = response.json()
            self.booking_id = booking_data.get('id')
            
            print("✅ Booking created successfully!")
            
            # Check for Zoom meeting details
            if 'zoom_meeting_id' in booking_data:
                print(f"   📹 Zoom Meeting ID: {booking_data.get('zoom_meeting_id')}")
                print(f"   🔗 Join URL: {booking_data.get('zoom_join_url', 'Not provided')}")
                print("   ✅ Zoom integration working!")
            else:
                print("   ⚠️  No Zoom meeting details in response")
                
        else:
            print(f"❌ Booking creation failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    def test_get_booking_details(self):
        """Test getting booking details"""
        url = f"{API_BASE}/bookings/bookings/{self.booking_id}/"
        
        response = requests.get(url, headers=self.get_headers('student'))
        
        if response.status_code == 200:
            booking = response.json()
            print("✅ Booking details retrieved successfully")
            
            if 'zoom_join_url' in booking:
                print("   📹 Zoom details present in booking")
        else:
            print(f"⚠️  Get booking details: {response.status_code}")
    
    def test_reschedule_booking(self):
        """Test rescheduling a booking (should update Zoom meeting)"""
        url = f"{API_BASE}/bookings/bookings/{self.booking_id}/reschedule/"
        tomorrow = datetime.now() + timedelta(days=1)
        new_start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        new_end_time = new_start_time + timedelta(hours=1)
        
        data = {
            "new_start_time": new_start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "new_end_time": new_end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "reason": "Testing reschedule functionality"
        }
        
        response = requests.post(url, json=data, headers=self.get_headers('student'))
        
        if response.status_code in [200, 204]:
            print("✅ Booking rescheduled successfully (Zoom meeting updated)")
        else:
            print(f"⚠️  Reschedule booking: {response.status_code}")
            print(f"Response: {response.text}")
    
    def test_get_my_bookings(self):
        """Test getting user's bookings"""
        url = f"{API_BASE}/bookings/bookings/my/"
        
        response = requests.get(url, headers=self.get_headers('student'))
        
        if response.status_code == 200:
            bookings = response.json()
            print(f"✅ My bookings retrieved: {len(bookings)} bookings found")
        else:
            print(f"⚠️  Get my bookings: {response.status_code}")

def main():
    """Run the tests"""
    print("🔧 Zoom Meeting API Test Suite")
    print("=" * 50)
    print("📋 Prerequisites:")
    print(f"   • Server running at {BASE_URL}")
    print(f"   • Teacher account: {TEACHER_CREDENTIALS['email']}")
    print(f"   • Student account: {STUDENT_CREDENTIALS['email']}")
    print(f"   • Zoom credentials configured in .env")
    print("=" * 50)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        if response.status_code in [200, 302]:
            print("✅ Server is running")
        else:
            print("❌ Server not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        return
    
    # Run tests
    tester = ZoomAPITester()
    tester.test_endpoints()
    
    print("=" * 50)
    print("🎯 Test completed! Now you can use Postman for detailed testing.")
    print("📁 Import: LinguaFlex_Zoom_API.postman_collection.json")

if __name__ == "__main__":
    main()
