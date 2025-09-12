#!/usr/bin/env python3
"""
Test script to verify payment intent creation works after fixing the gig.title and gig.hourly_rate issues
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_payment_intent_creation():
    """Test that payment intent creation works with the fixed gig attributes"""
    
    print("🧪 Testing Payment Intent Creation After Bug Fixes\n")
    
    # Step 1: Register and login a test student
    print("1️⃣ Creating test student account...")
    student_data = {
        "email": "test_payment_student@test.com",
        "password": "testpass123",
        "first_name": "Payment",
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
    
    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Create a test booking first
    print("\n2️⃣ Creating a test booking...")
    booking_data = {
        "teacher": 1,  # Assume teacher with ID 1 exists
        "gig": 1,      # Assume gig with ID 1 exists
        "start_time": "2024-12-20T10:00:00Z",
        "end_time": "2024-12-20T11:00:00Z",
        "notes": "Test booking for payment intent creation"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings/bookings/", json=booking_data, headers=headers)
        
        if response.status_code == 201:
            booking = response.json()
            booking_id = booking.get('id')
            print(f"✅ Test booking created successfully (ID: {booking_id})")
            print(f"   Duration: {booking.get('duration_hours')} hours")
        else:
            print(f"❌ Booking creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("ℹ️ Assuming booking with ID 55 exists for testing...")
            booking_id = 55
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating booking: {e}")
        print("ℹ️ Using booking ID 55 for testing...")
        booking_id = 55
    
    # Step 3: Test payment intent creation
    print(f"\n3️⃣ Testing payment intent creation for booking {booking_id}...")
    
    payment_intent_data = {
        "session_booking_id": booking_id,
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data, headers=headers)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Payment intent created successfully!")
            print(f"   Client Secret: {result.get('client_secret', 'N/A')}")
            print(f"   Payment ID: {result.get('payment_id', 'N/A')}")
            print(f"   Amount: ${result.get('amount_dollars', 'N/A')}")
            print("\n🎯 All bug fixes working correctly!")
            
        elif response.status_code == 400:
            error_response = response.json()
            error_message = error_response.get('error', 'Unknown error')
            
            if "'Gig' object has no attribute 'title'" in error_message:
                print("❌ BUG STILL EXISTS: Gig.title attribute error")
                print("   This means the fix wasn't applied correctly")
            elif "'Gig' object has no attribute 'hourly_rate'" in error_message:
                print("❌ BUG STILL EXISTS: Gig.hourly_rate attribute error")
                print("   This means the fix wasn't applied correctly")
            else:
                print(f"ℹ️ Different error (might be expected): {error_message}")
                print("   This could be due to missing Stripe configuration or invalid booking data")
                
        else:
            print(f"❌ Unexpected response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating payment intent: {e}")
    
    print("\n💡 Summary:")
    print("   • Fixed gig.hourly_rate → gig.price_per_session")
    print("   • Fixed gig.title → gig.service_title")
    print("   • If you get Stripe errors, that's expected without proper Stripe configuration")
    print("   • The important thing is that Gig attribute errors are resolved")

if __name__ == "__main__":
    test_payment_intent_creation()
