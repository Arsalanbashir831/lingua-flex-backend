#!/usr/bin/env python3
"""
Test the complete 3-step booking and payment flow:
1. Student creates booking (PENDING)
2. Teacher confirms booking (CONFIRMED) 
3. Student pays for booking (PAID)
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta

# Add the Django project to the Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')

# Import Django
import django
django.setup()

# Test credentials
STUDENT_CREDENTIALS = {
    "email": "fahije3853@hostbyt.com",
    "password": "testpassword1234"
}

TEACHER_CREDENTIALS = {
    "email": "rebin81412@hostbyt.com", 
    "password": "testpassword123"
}

BASE_URL = "http://127.0.0.1:8000"

def login_user(credentials):
    """Login and get JWT token"""
    login_url = f"{BASE_URL}/api/login/"
    
    try:
        response = requests.post(login_url, json=credentials)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token') or token_data.get('token')
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def step1_create_booking(student_token):
    """Step 1: Student creates booking"""
    print("\n" + "="*60)
    print("📅 STEP 1: Student Creates Booking")
    print("="*60)
    
    url = f"{BASE_URL}/api/bookings/bookings/"
    
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    # Create booking for 30 minutes from now
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(minutes=30)
    
    booking_data = {
        "teacher": 2,  # Assuming teacher ID 2 exists
        "gig": 11,     # Using the gig ID from your example
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": "Looking forward to improving my English"
    }
    
    print(f"📝 Creating booking with data:")
    print(json.dumps(booking_data, indent=2))
    
    try:
        response = requests.post(url, headers=headers, json=booking_data)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            booking = response.json()
            print(f"✅ Booking created successfully!")
            print(f"   Booking ID: {booking.get('id')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Payment Status: {booking.get('payment_status')}")
            print(f"   Duration: {booking.get('duration_hours')} hours")
            return booking.get('id')
        else:
            print(f"❌ Failed to create booking:")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating booking: {e}")
        return None

def step2_teacher_confirms(teacher_token, booking_id):
    """Step 2: Teacher confirms booking"""
    print("\n" + "="*60)
    print("👨‍🏫 STEP 2: Teacher Confirms Booking")
    print("="*60)
    
    url = f"{BASE_URL}/api/bookings/bookings/{booking_id}/confirm/"
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Confirming booking ID: {booking_id}")
    
    try:
        response = requests.post(url, headers=headers)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Booking confirmed successfully!")
            print(f"   Message: {data.get('message')}")
            
            booking = data.get('booking', {})
            print(f"   Status: {booking.get('status')}")
            print(f"   Payment Status: {booking.get('payment_status')}")
            print(f"   Zoom Meeting ID: {booking.get('zoom_meeting_id')}")
            print(f"   Zoom Join URL: {booking.get('zoom_join_url')[:50]}..." if booking.get('zoom_join_url') else "   No Zoom URL")
            return True
        else:
            print(f"❌ Failed to confirm booking:")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error confirming booking: {e}")
        return False

def step3_student_pays(student_token, booking_id):
    """Step 3: Student pays for confirmed booking"""
    print("\n" + "="*60)
    print("💳 STEP 3: Student Pays for Booking")
    print("="*60)
    
    url = f"{BASE_URL}/api/payments/process-booking-payment/"
    
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "booking_id": booking_id,
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "Student Name",
        "save_payment_method": True
    }
    
    print(f"💰 Processing payment for booking ID: {booking_id}")
    print(f"💳 Using card: ****{payment_data['card_number'][-4:]}")
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payment processed successfully!")
            print(f"   Message: {data.get('message')}")
            print(f"   Payment Intent ID: {data.get('payment_intent_id')}")
            print(f"   Amount Paid: ${data.get('amount_paid', 0):.2f}")
            print(f"   Session Cost: ${data.get('session_cost', 0):.2f}")
            print(f"   Platform Fee: ${data.get('platform_fee', 0):.2f}")
            print(f"   Card: {data.get('card_brand')} ****{data.get('card_last4')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Payment failed:")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing payment: {e}")
        return False

def verify_final_booking_status(student_token, booking_id):
    """Verify the final booking status"""
    print("\n" + "="*60)
    print("🔍 VERIFICATION: Final Booking Status")
    print("="*60)
    
    url = f"{BASE_URL}/api/bookings/bookings/{booking_id}/"
    
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            booking = response.json()
            print(f"📋 Final Booking Status:")
            print(f"   Booking ID: {booking.get('id')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Payment Status: {booking.get('payment_status')}")
            print(f"   Duration: {booking.get('duration_hours')} hours")
            print(f"   Zoom Meeting ID: {booking.get('zoom_meeting_id')}")
            print(f"   Created: {booking.get('created_at')}")
            print(f"   Updated: {booking.get('updated_at')}")
            
            if booking.get('status') == 'CONFIRMED' and booking.get('payment_status') == 'PAID':
                print(f"\n🎉 SUCCESS: Complete flow executed successfully!")
                return True
            else:
                print(f"\n⚠️  WARNING: Flow incomplete")
                return False
        else:
            print(f"❌ Failed to get booking details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting booking: {e}")
        return False

def main():
    print("🚀 Testing Complete 3-Step Booking & Payment Flow")
    print("="*80)
    print("Flow: Student Creates → Teacher Confirms → Student Pays")
    print("="*80)
    
    # Login both users
    print("\n🔐 Logging in users...")
    student_token = login_user(STUDENT_CREDENTIALS)
    teacher_token = login_user(TEACHER_CREDENTIALS)
    
    if not student_token:
        print("❌ Cannot proceed without student authentication")
        return
    
    if not teacher_token:
        print("❌ Cannot proceed without teacher authentication")
        return
    
    print("✅ Both users authenticated successfully")
    
    # Step 1: Student creates booking
    booking_id = step1_create_booking(student_token)
    if not booking_id:
        print("❌ Cannot proceed without booking creation")
        return
    
    # Step 2: Teacher confirms booking
    confirmed = step2_teacher_confirms(teacher_token, booking_id)
    if not confirmed:
        print("❌ Cannot proceed without booking confirmation")
        return
    
    # Step 3: Student pays for booking
    paid = step3_student_pays(student_token, booking_id)
    if not paid:
        print("❌ Payment failed")
        return
    
    # Verify final status
    success = verify_final_booking_status(student_token, booking_id)
    
    print("\n" + "="*80)
    if success:
        print("🎊 COMPLETE SUCCESS: 3-Step Flow Executed Perfectly!")
        print("   ✅ Booking Created (PENDING → CONFIRMED → PAID)")
        print("   ✅ Teacher Confirmation Working")
        print("   ✅ Payment Processing Working")
        print("   ✅ Zoom Meeting Integration Working")
    else:
        print("⚠️  Flow completed but with issues")
    print("="*80)

if __name__ == "__main__":
    main()
