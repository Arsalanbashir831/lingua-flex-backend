#!/usr/bin/env python3
"""
Test the booking payment flow with the fixed PaymentIntent configuration
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

def create_booking(token, teacher_id=None, gig_id=None):
    """Create a booking session"""
    url = "http://127.0.0.1:8000/api/bookings/bookings/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Default test booking data
    now = datetime.now()
    start_time = now + timedelta(days=1)  # Tomorrow
    end_time = start_time + timedelta(minutes=30)  # 30 minute session
    
    booking_data = {
        "teacher": teacher_id or 5,  # Default teacher ID
        "gig": gig_id or 11,         # Default gig ID  
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": "Test booking for payment flow"
    }
    
    try:
        response = requests.post(url, headers=headers, json=booking_data)
        print(f"Create Booking Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            booking = response.json()
            print(f"✓ Booking created successfully")
            print(f"  Booking ID: {booking.get('id')}")
            print(f"  Status: {booking.get('status')}")
            print(f"  Payment Status: {booking.get('payment_status')}")
            print(f"  Duration: {booking.get('duration_hours')} hours")
            return booking
        else:
            print(f"✗ Failed to create booking: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Booking creation error: {e}")
        return None

def process_booking_payment(token, booking_id):
    """Process payment for the booking"""
    url = "http://127.0.0.1:8000/api/payments/process-booking-payment/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "booking_id": booking_id,
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "Test Student",
        "save_payment_method": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"\nPayment Status: {response.status_code}")
        print(f"Payment Response: {response.text}")
        
        if response.status_code == 200:
            payment = response.json()
            print(f"✓ Payment processed successfully!")
            print(f"  Payment Intent ID: {payment.get('payment_intent_id')}")
            print(f"  Amount Paid: ${payment.get('amount_paid')}")
            print(f"  Session Cost: ${payment.get('session_cost')}")
            print(f"  Platform Fee: ${payment.get('platform_fee')}")
            print(f"  Card: {payment.get('card_brand')} ****{payment.get('card_last4')}")
            print(f"  Status: {payment.get('status')}")
            if payment.get('zoom_join_url'):
                print(f"  Zoom URL: {payment.get('zoom_join_url')}")
            return True
        else:
            print(f"✗ Payment failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Payment error: {e}")
        return False

def test_with_saved_payment_method(token, booking_id, payment_method_id):
    """Test payment with saved payment method"""
    url = "http://127.0.0.1:8000/api/payments/process-booking-payment/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "booking_id": booking_id,
        "saved_payment_method_id": payment_method_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"\nSaved Payment Status: {response.status_code}")
        
        if response.status_code == 200:
            payment = response.json()
            print(f"✓ Payment with saved method successful!")
            print(f"  Amount Paid: ${payment.get('amount_paid')}")
            return True
        else:
            print(f"✗ Saved payment failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Saved payment error: {e}")
        return False

def get_saved_payment_methods(token):
    """Get saved payment methods"""
    url = "http://127.0.0.1:8000/api/payments/payment-methods/"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            methods = response.json()
            if methods:
                print(f"\n📋 Found {len(methods)} saved payment methods:")
                for method in methods:
                    print(f"  - {method.get('card_brand')} ****{method.get('card_last_four')} (ID: {method.get('stripe_payment_method_id')})")
                return methods[0].get('stripe_payment_method_id')  # Return first method ID
            else:
                print(f"\n📋 No saved payment methods found")
                return None
        else:
            print(f"✗ Failed to get payment methods: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error getting payment methods: {e}")
        return None

def main():
    print("🚀 Testing Complete Booking Payment Flow")
    print("=" * 60)
    
    # Test credentials
    student_email = "fahije3853@hostbyt.com"
    student_password = "testpassword1234"
    
    # 1. Login as student
    print("🔐 Step 1: Student Login")
    token = login_user(student_email, student_password)
    if not token:
        print("✗ Cannot proceed without authentication")
        return
    
    print(f"✓ Student authenticated successfully")
    
    # 2. Create booking
    print(f"\n📅 Step 2: Creating Booking Session")
    booking = create_booking(token)
    if not booking:
        print("✗ Cannot proceed without booking")
        return
    
    booking_id = booking.get('id')
    
    # 3. Process payment for booking
    print(f"\n💳 Step 3: Processing Payment for Booking {booking_id}")
    payment_success = process_booking_payment(token, booking_id)
    
    if not payment_success:
        print("✗ Payment failed - stopping test")
        return
    
    # 4. Check saved payment methods
    print(f"\n💾 Step 4: Checking Saved Payment Methods")
    saved_pm_id = get_saved_payment_methods(token)
    
    # 5. Test with saved payment method (create another booking)
    if saved_pm_id:
        print(f"\n🔄 Step 5: Testing Payment with Saved Method")
        booking2 = create_booking(token)
        if booking2:
            test_with_saved_payment_method(token, booking2.get('id'), saved_pm_id)
    
    print(f"\n🎉 Complete booking payment flow test completed!")
    print("✅ All steps successful!")

if __name__ == "__main__":
    main()
