#!/usr/bin/env python3
"""
Test the complete booking and payment flow to verify Zoom URLs are preserved
"""

import requests
import json
import os
import sys

# Add the Django project to the Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')

# Import Django
import django
django.setup()

# Now import Django models
from core.models import User

def login_user(email, password):
    """Login and get JWT token"""
    login_url = "http://127.0.0.1:8000/api/login/"
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token') or token_data.get('token')
        else:
            print(f"✗ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login error: {e}")
        return None

def step_1_create_booking(student_token, teacher_id, gig_id):
    """Step 1: Student creates booking"""
    url = "http://127.0.0.1:8000/api/bookings/bookings/"
    
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    booking_data = {
        "teacher": teacher_id,
        "gig": gig_id,
        "start_time": "2024-12-20T10:00:00Z",
        "end_time": "2024-12-20T10:30:00Z",
        "notes": "Looking forward to improving my English"
    }
    
    try:
        response = requests.post(url, headers=headers, json=booking_data)
        print(f"📅 Step 1 - Create Booking")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            booking_id = data['id']
            print(f"✓ Booking created successfully!")
            print(f"  Booking ID: {booking_id}")
            print(f"  Status: {data.get('status')}")
            print(f"  Payment Status: {data.get('payment_status')}")
            print(f"  Zoom Meeting ID: {data.get('zoom_meeting_id', 'Not set')}")
            print(f"  Zoom Join URL: {data.get('zoom_join_url', 'Not set')}")
            return booking_id, data.get('zoom_join_url'), data.get('zoom_meeting_id')
        else:
            print(f"✗ Failed: {response.text}")
            return None, None, None
            
    except Exception as e:
        print(f"✗ Request error: {e}")
        return None, None, None

def step_2_teacher_confirm(teacher_token, booking_id):
    """Step 2: Teacher confirms booking"""
    url = f"http://127.0.0.1:8000/api/bookings/bookings/{booking_id}/confirm/"
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers)
        print(f"\n✅ Step 2 - Teacher Confirms Booking")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Booking confirmed successfully!")
            print(f"  Message: {data.get('message')}")
            
            # Get updated booking details
            booking_url = f"http://127.0.0.1:8000/api/bookings/bookings/{booking_id}/"
            booking_response = requests.get(booking_url, headers=headers)
            if booking_response.status_code == 200:
                booking_data = booking_response.json()
                print(f"  Status: {booking_data.get('status')}")
                print(f"  Payment Status: {booking_data.get('payment_status')}")
                print(f"  Zoom Meeting ID: {booking_data.get('zoom_meeting_id', 'Not set')}")
                print(f"  Zoom Join URL: {booking_data.get('zoom_join_url', 'Not set')}")
                return booking_data.get('zoom_join_url'), booking_data.get('zoom_meeting_id')
            
            return None, None
        else:
            print(f"✗ Failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Request error: {e}")
        return None, None

def step_3_student_payment(student_token, booking_id):
    """Step 3: Student makes payment"""
    url = "http://127.0.0.1:8000/api/payments/process-booking-payment/"
    
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
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"\n💳 Step 3 - Student Makes Payment")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Payment processed successfully!")
            print(f"  Payment ID: {data.get('payment_id')}")
            print(f"  Amount Paid: ${data.get('amount_paid')}")
            print(f"  Status: {data.get('status')}")
            print(f"  Card: {data.get('card_brand')} ****{data.get('card_last4')}")
            print(f"  Zoom Join URL: {data.get('zoom_join_url', 'Not set')}")
            return data.get('zoom_join_url')
        else:
            print(f"✗ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Request error: {e}")
        return None

def main():
    print("🧪 Testing Complete Booking and Payment Flow with Zoom URL Preservation")
    print("=" * 80)
    
    # Test credentials
    student_email = "fahije3853@hostbyt.com"
    student_password = "testpassword1234"
    teacher_email = "rebin81412@hostbyt.com"
    teacher_password = "testpassword123"
    
    # Login both users
    print("🔐 Logging in users...")
    student_token = login_user(student_email, student_password)
    teacher_token = login_user(teacher_email, teacher_password)
    
    if not student_token or not teacher_token:
        print("✗ Cannot proceed without authentication tokens")
        return
    
    print("✓ Both users logged in successfully")
    
    # Test parameters (you may need to adjust these)
    teacher_id = 2  # Adjust based on your data
    gig_id = 11     # Adjust based on your data
    
    # Step 1: Student creates booking
    booking_id, initial_zoom_url, initial_meeting_id = step_1_create_booking(
        student_token, teacher_id, gig_id
    )
    
    if not booking_id:
        print("✗ Cannot proceed without booking")
        return
    
    # Step 2: Teacher confirms booking (this should create Zoom meeting)
    confirmed_zoom_url, confirmed_meeting_id = step_2_teacher_confirm(
        teacher_token, booking_id
    )
    
    # Step 3: Student makes payment (this should NOT change Zoom URL)
    final_zoom_url = step_3_student_payment(student_token, booking_id)
    
    # Verify Zoom URL preservation
    print(f"\n🔍 Zoom URL Verification:")
    print(f"  Initial Zoom URL: {initial_zoom_url}")
    print(f"  After Confirmation: {confirmed_zoom_url}")
    print(f"  After Payment: {final_zoom_url}")
    
    if confirmed_zoom_url and final_zoom_url:
        if confirmed_zoom_url == final_zoom_url:
            print("✅ SUCCESS: Zoom URL preserved correctly!")
        else:
            print("❌ ISSUE: Zoom URL changed during payment!")
    elif confirmed_zoom_url:
        print("✅ Zoom URL created during confirmation as expected")
    else:
        print("⚠️  No Zoom URL found")
    
    print(f"\n🎉 Complete flow test finished!")

if __name__ == "__main__":
    main()
