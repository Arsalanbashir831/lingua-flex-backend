#!/usr/bin/env python3
"""
Test the booking payment flow after fixing the Stripe PaymentIntent configuration
"""

import requests
import json
import os
import sys

# Add the Django project to the Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')

import django
django.setup()

from core.models import User

def login_user():
    """Login and get JWT token"""
    login_url = "http://127.0.0.1:8000/api/login/"
    
    login_data = {
        "email": "fahije3853@hostbyt.com",  # Student credentials
        "password": "testpassword1234"
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

def test_booking_payment(token, booking_id):
    """Test paying for an existing booking"""
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
        "cardholder_name": "Student Name",
        "save_payment_method": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"Payment Status: {response.status_code}")
        print(f"Payment Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Payment successful!")
            print(f"  Payment Intent ID: {data.get('payment_intent_id')}")
            print(f"  Booking ID: {data.get('booking_id')}")
            print(f"  Amount Paid: ${data.get('amount_paid')}")
            print(f"  Card: {data.get('card_brand')} ****{data.get('card_last4')}")
            return True
        else:
            print(f"✗ Payment failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Payment error: {e}")
        return False

def create_test_booking(token):
    """Create a test booking first"""
    url = "http://127.0.0.1:8000/api/bookings/bookings/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    booking_data = {
        "teacher": 2,  # Adjust this to a valid teacher ID
        "gig": 11,
        "start_time": "2024-12-20T10:00:00Z",
        "end_time": "2024-12-20T10:30:00Z",
        "notes": "Looking forward to improving my English"
    }
    
    try:
        response = requests.post(url, headers=headers, json=booking_data)
        print(f"Booking Status: {response.status_code}")
        print(f"Booking Response: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✓ Booking created successfully!")
            print(f"  Booking ID: {data.get('id')}")
            return data.get('id')
        else:
            print(f"✗ Booking failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Booking error: {e}")
        return None

def main():
    print("🚀 Testing Fixed Booking Payment Flow")
    print("=" * 50)
    
    # Login
    print("🔐 Logging in...")
    token = login_user()
    if not token:
        print("✗ Cannot proceed without authentication")
        return
    
    print(f"✓ Authenticated successfully")
    
    # Create a test booking first (if needed)
    print(f"\n📅 Creating test booking...")
    booking_id = create_test_booking(token)
    if not booking_id:
        # Use existing booking ID if creation fails
        booking_id = 61
        print(f"⚠️  Using existing booking ID: {booking_id}")
    
    # Test payment for the booking
    print(f"\n💳 Processing payment for booking {booking_id}...")
    payment_success = test_booking_payment(token, booking_id)
    
    if payment_success:
        print(f"\n🎉 Booking payment flow successful!")
    else:
        print(f"\n❌ Payment processing failed")
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    main()
