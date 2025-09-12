#!/usr/bin/env python3
"""
Test the complete booking and payment flow:
1. Student creates booking session
2. Student processes payment for the booking
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

def create_booking_session(token, teacher_id, gig_id):
    """Create a booking session"""
    url = "http://127.0.0.1:8000/api/bookings/bookings/"
    
    headers = {
        "Authorization": f"Bearer {token}",
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
        print(f"Booking Status: {response.status_code}")
        print(f"Booking Response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            booking_id = data.get('id')
            print(f"✓ Booking created successfully with ID: {booking_id}")
            return booking_id, data
        else:
            print(f"✗ Failed to create booking: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Booking creation error: {e}")
        return None, None

def process_booking_payment(token, booking_id):
    """Process payment for an existing booking"""
    url = "http://127.0.0.1:8000/api/payments/process-booking-payment/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with different cards
    test_cards = [
        {
            "name": "Visa Success",
            "payment_data": {
                "booking_id": booking_id,
                "card_number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
                "cardholder_name": "Student User",
                "save_payment_method": True
            }
        }
    ]
    
    for card in test_cards:
        print(f"\n💳 Testing payment with {card['name']}...")
        
        try:
            response = requests.post(url, headers=headers, json=card['payment_data'])
            print(f"Payment Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Payment successful!")
                print(f"  Payment ID: {data.get('payment_id')}")
                print(f"  Amount Paid: ${data.get('amount_paid')}")
                print(f"  Session Cost: ${data.get('session_cost')}")
                print(f"  Platform Fee: ${data.get('platform_fee')}")
                print(f"  Duration: {data.get('duration_hours')} hours")
                print(f"  Hourly Rate: ${data.get('hourly_rate')}")
                print(f"  Card: {data.get('card_brand')} ending in {data.get('card_last4')}")
                if data.get('zoom_join_url'):
                    print(f"  Zoom URL: {data.get('zoom_join_url')}")
                
                booking_details = data.get('booking_details', {})
                print(f"  Teacher: {booking_details.get('teacher_name')}")
                print(f"  Session: {booking_details.get('start_time')} to {booking_details.get('end_time')}")
                
                return True
            else:
                print(f"✗ Payment failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Payment error: {e}")
            return False

def get_available_gigs(token):
    """Get available gigs for testing"""
    url = "http://127.0.0.1:8000/api/accounts/gigs/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            gigs = response.json()
            if isinstance(gigs, dict) and 'results' in gigs:
                gigs = gigs['results']
            
            print(f"📋 Available gigs:")
            for gig in gigs[:3]:  # Show first 3 gigs
                teacher_name = "Unknown"
                if isinstance(gig.get('teacher'), dict):
                    teacher_name = gig['teacher'].get('name', 'Unknown')
                
                print(f"  - Gig ID: {gig.get('id')}, Teacher: {teacher_name}, Price: ${gig.get('price_per_session', 'N/A')}")
            
            return gigs[0] if gigs else None  # Return first gig for testing
        else:
            print(f"✗ Failed to get gigs: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error getting gigs: {e}")
        return None

def main():
    print("🚀 Testing Complete Booking and Payment Flow")
    print("=" * 60)
    
    # Login as student
    student_email = "fahije3853@hostbyt.com"
    student_password = "testpassword1234"
    
    print(f"🔐 Logging in as student: {student_email}")
    student_token = login_user(student_email, student_password)
    if not student_token:
        print("✗ Cannot proceed without student authentication")
        return
    
    print(f"✓ Student authenticated successfully")
    
    # Get available gigs
    print(f"\n📚 Getting available gigs...")
    gig = get_available_gigs(student_token)
    if not gig:
        print("✗ No gigs available for testing")
        return
    
    gig_id = gig.get('id')
    teacher_info = gig.get('teacher', {})
    teacher_id = teacher_info.get('id') if isinstance(teacher_info, dict) else teacher_info
    
    print(f"✓ Using Gig ID: {gig_id}, Teacher ID: {teacher_id}")
    
    # Step 1: Create booking session
    print(f"\n📅 Step 1: Creating booking session...")
    booking_id, booking_data = create_booking_session(student_token, teacher_id, gig_id)
    if not booking_id:
        print("✗ Cannot proceed without booking")
        return
    
    print(f"✓ Booking created with ID: {booking_id}")
    print(f"  Status: {booking_data.get('status', 'Unknown')}")
    print(f"  Payment Status: {booking_data.get('payment_status', 'Unknown')}")
    
    # Step 2: Process payment for booking
    print(f"\n💰 Step 2: Processing payment for booking...")
    payment_success = process_booking_payment(student_token, booking_id)
    
    if payment_success:
        print(f"\n🎉 Complete booking and payment flow successful!")
        print(f"✅ Flow Summary:")
        print(f"  1. ✓ Student logged in")
        print(f"  2. ✓ Booking session created (ID: {booking_id})")
        print(f"  3. ✓ Payment processed successfully")
        print(f"  4. ✓ Booking confirmed and ready for session")
    else:
        print(f"\n⚠️  Booking created but payment failed")
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    main()
