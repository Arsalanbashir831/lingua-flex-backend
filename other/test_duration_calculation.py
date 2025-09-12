#!/usr/bin/env python3
"""
Test script to verify automatic duration calculation in booking creation
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_duration_calculation():
    """Test that duration_hours is automatically calculated from start_time and end_time"""
    
    print("🧪 Testing Automatic Duration Calculation for Booking Creation\n")
    
    # Test cases with different durations
    test_cases = [
        {
            "name": "20-minute session",
            "start_time": "2024-12-20T10:00:00Z",
            "end_time": "2024-12-20T10:20:00Z",
            "expected_duration": 0.33  # 20 minutes = 0.33 hours (rounded)
        },
        {
            "name": "1-hour session", 
            "start_time": "2024-12-20T14:00:00Z",
            "end_time": "2024-12-20T15:00:00Z",
            "expected_duration": 1.0
        },
        {
            "name": "1.5-hour session",
            "start_time": "2024-12-20T16:00:00Z", 
            "end_time": "2024-12-20T17:30:00Z",
            "expected_duration": 1.5
        },
        {
            "name": "45-minute session",
            "start_time": "2024-12-20T09:00:00Z",
            "end_time": "2024-12-20T09:45:00Z", 
            "expected_duration": 0.75
        }
    ]
    
    # Step 1: Register and login a test student
    print("1️⃣ Creating test student account...")
    student_data = {
        "email": "test_student_duration@test.com",
        "password": "testpass123",
        "first_name": "Duration",
        "last_name": "Tester",
        "user_type": "student"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register/", json=student_data)
        if response.status_code == 201:
            print("✅ Student account created successfully")
        else:
            print("ℹ️ Student account might already exist, trying to login...")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating student: {e}")
        return
    
    # Login student
    login_data = {
        "email": student_data["email"],
        "password": student_data["password"]
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
        if response.status_code == 200:
            student_token = response.json()["access_token"]
            print("✅ Student logged in successfully")
        else:
            print(f"❌ Student login failed: {response.text}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Error logging in student: {e}")
        return
    
    # Step 2: Create teacher and gig (simplified - assume they exist with IDs 1 and 1)
    print("\n2️⃣ Testing duration calculation for different time spans...\n")
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    # Test each duration case
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"   Start: {test_case['start_time']}")
        print(f"   End: {test_case['end_time']}")
        print(f"   Expected Duration: {test_case['expected_duration']} hours")
        
        # Create booking data WITHOUT duration_hours field
        booking_data = {
            "teacher": 1,  # Assume teacher with ID 1 exists
            "gig": 1,      # Assume gig with ID 1 exists
            "start_time": test_case['start_time'],
            "end_time": test_case['end_time'],
            "notes": f"Test booking for {test_case['name']}"
        }
        
        try:
            response = requests.post(f"{API_BASE}/bookings/bookings/", json=booking_data, headers=headers)
            
            if response.status_code == 201:
                booking = response.json()
                calculated_duration = float(booking.get('duration_hours', 0))
                
                print(f"   ✅ Booking created successfully")
                print(f"   📊 Calculated Duration: {calculated_duration} hours")
                
                # Verify duration is correct (allow small rounding differences)
                if abs(calculated_duration - test_case['expected_duration']) < 0.01:
                    print(f"   ✅ Duration calculation CORRECT!")
                else:
                    print(f"   ❌ Duration calculation INCORRECT! Expected {test_case['expected_duration']}, got {calculated_duration}")
                
                print(f"   📋 Booking ID: {booking.get('id')}")
                
            else:
                print(f"   ❌ Booking creation failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error creating booking: {e}")
        
        print()  # Empty line for readability
    
    print("🎯 Duration calculation testing completed!")
    print("\n💡 Key Points:")
    print("   • duration_hours is automatically calculated from start_time and end_time")
    print("   • No need to include duration_hours in the request body")
    print("   • scheduled_datetime is also auto-set to start_time if not provided")

if __name__ == "__main__":
    test_duration_calculation()
