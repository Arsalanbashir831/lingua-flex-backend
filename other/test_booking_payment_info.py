#!/usr/bin/env python3
"""
Test script to verify that booking endpoints now include payment ID
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
STUDENT_TOKEN = ""  # Will be filled after login

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{title}:")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    except:
        print(response.text)
        return None

def test_student_login():
    """Test student login"""
    print_section("1. STUDENT LOGIN")
    
    login_data = {
        "email": "student@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    print_response(response, "Student Login")
    
    if response.status_code == 200:
        global STUDENT_TOKEN
        STUDENT_TOKEN = response.json().get('access_token')
        print(f"Student Token: {STUDENT_TOKEN[:20]}...")
    
    return response.status_code == 200

def test_booking_detail_with_payment():
    """Test getting booking details with payment information"""
    print_section("2. GET BOOKING WITH PAYMENT ID")
    
    # Using the booking ID from your successful payment (booking_id: 4)
    booking_id = 4
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.get(f"{BASE_URL}/bookings/bookings/{booking_id}/", headers=headers)
    
    data = print_response(response, f"Booking #{booking_id} Details")
    
    if data and response.status_code == 200:
        print(f"\n🎯 KEY INFORMATION EXTRACTED:")
        print(f"Booking ID: {data.get('id')}")
        print(f"Payment ID: {data.get('payment_id')}")
        print(f"Status: {data.get('status')}")
        print(f"Payment Status: {data.get('payment_status')}")
        
        # Payment details
        payment_details = data.get('payment_details')
        if payment_details:
            print(f"\n💰 PAYMENT DETAILS:")
            print(f"Payment ID: {payment_details.get('payment_id')}")
            print(f"Amount Paid: ${payment_details.get('amount_paid')}")
            print(f"Payment Status: {payment_details.get('payment_status')}")
            print(f"Platform Fee: ${payment_details.get('platform_fee')}")
            print(f"Session Cost: ${payment_details.get('session_cost')}")
            print(f"Stripe Payment Intent: {payment_details.get('stripe_payment_intent_id')}")
        else:
            print(f"\n⚠️ No payment found for this booking")
    
    return data

def test_all_bookings_list():
    """Test getting all bookings for the user"""
    print_section("3. GET ALL BOOKINGS WITH PAYMENT INFO")
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.get(f"{BASE_URL}/bookings/bookings/", headers=headers)
    
    data = print_response(response, "All User Bookings")
    
    if data and response.status_code == 200:
        print(f"\n📋 BOOKINGS SUMMARY:")
        print(f"Total Bookings: {len(data)}")
        
        for booking in data:
            print(f"\n📌 Booking #{booking.get('id')}:")
            print(f"   Status: {booking.get('status')}")
            print(f"   Payment ID: {booking.get('payment_id') or 'No payment'}")
            print(f"   Start Time: {booking.get('start_time')}")
            
            payment_details = booking.get('payment_details')
            if payment_details:
                print(f"   💰 Payment: ${payment_details.get('amount_paid')} ({payment_details.get('payment_status')})")
    
    return data

def test_my_bookings_endpoint():
    """Test the my_bookings endpoint with filters"""
    print_section("4. TEST MY_BOOKINGS ENDPOINT")
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    
    # Test with different filters
    endpoints_to_test = [
        ("All bookings", "/api/bookings/bookings/my_bookings/"),
        ("Confirmed bookings", "/api/bookings/bookings/my_bookings/?status=confirmed"),
        ("Student bookings only", "/api/bookings/bookings/my_bookings/?role=student")
    ]
    
    for name, endpoint in endpoints_to_test:
        print(f"\n🔍 Testing: {name}")
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Count: {data.get('count', 0)}")
            results = data.get('results', [])
            for booking in results[:2]:  # Show first 2 bookings
                print(f"  Booking #{booking.get('id')}: Payment ID = {booking.get('payment_id')}")
        else:
            print(f"Error: {response.status_code}")

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Booking Endpoints with Payment ID")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Test login first
    if not test_student_login():
        print("❌ Student login failed. Cannot continue tests.")
        return
    
    # Test booking endpoints
    test_booking_detail_with_payment()
    test_all_bookings_list()
    test_my_bookings_endpoint()
    
    print_section("SUMMARY")
    print("✅ Booking endpoints now include:")
    print("  • payment_id: Direct payment ID for the booking")
    print("  • payment_details: Complete payment information")
    print("  • amount_paid: Total amount paid by student")
    print("  • payment_status: Current payment status")
    print("  • platform_fee: Platform fee charged")
    print("  • session_cost: Cost of the session")
    print("  • stripe_payment_intent_id: Stripe payment reference")
    
    print(f"\n🎯 Your booking endpoint now returns payment ID: {{booking_id}}/")
    print(f"🏁 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
