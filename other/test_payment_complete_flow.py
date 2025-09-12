#!/usr/bin/env python3
"""
Test script to verify payment intent creation and confirmation after fixing redirect issues
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_complete_payment_flow():
    """Test the complete payment flow including intent creation and confirmation"""
    
    print("🧪 Testing Complete Payment Flow (Intent Creation + Confirmation)\n")
    
    # Step 1: Register and login a test student
    print("1️⃣ Creating test student account...")
    student_data = {
        "email": "test_payment_flow@test.com",
        "password": "testpass123",
        "first_name": "Payment",
        "last_name": "FlowTester",
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
    
    # Step 2: Test Payment Intent Creation
    print("\n2️⃣ Testing payment intent creation...")
    
    payment_intent_data = {
        "session_booking_id": 55,  # Using the booking ID from your test
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
            
            # Extract payment intent ID from client secret
            client_secret = result.get('client_secret', '')
            if '_secret_' in client_secret:
                payment_intent_id = client_secret.split('_secret_')[0]
                print(f"   Payment Intent ID: {payment_intent_id}")
                
                # Step 3: Test Payment Confirmation
                print("\n3️⃣ Testing payment confirmation...")
                confirm_data = {
                    "payment_intent_id": payment_intent_id
                }
                
                try:
                    confirm_response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
                    
                    print(f"📊 Confirmation Response Status: {confirm_response.status_code}")
                    
                    if confirm_response.status_code == 200:
                        confirm_result = confirm_response.json()
                        print("✅ Payment confirmation attempted successfully!")
                        print(f"   Status: {confirm_result.get('status', 'N/A')}")
                        print(f"   Requires Action: {confirm_result.get('requires_action', 'N/A')}")
                        
                        if confirm_result.get('status') == 'requires_payment_method':
                            print("ℹ️ Payment requires a valid payment method to be attached")
                            print("   This is expected in test mode without a real card")
                        elif confirm_result.get('status') == 'succeeded':
                            print("🎉 Payment completed successfully!")
                        else:
                            print(f"ℹ️ Payment status: {confirm_result.get('status')}")
                            
                    else:
                        error_response = confirm_response.json() if confirm_response.status_code == 400 else {"error": confirm_response.text}
                        error_message = error_response.get('error', 'Unknown error')
                        
                        if "return_url" in error_message.lower():
                            print("❌ RETURN_URL ERROR STILL EXISTS:")
                            print(f"   {error_message}")
                            print("   The fix for redirect-based payment methods didn't work")
                        else:
                            print(f"ℹ️ Different confirmation error: {error_message}")
                            print("   This might be due to missing payment method or Stripe test configuration")
                            
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error confirming payment: {e}")
            else:
                print("❌ Could not extract payment intent ID from client secret")
                
        else:
            error_response = response.json() if response.status_code == 400 else {"error": response.text}
            error_message = error_response.get('error', 'Unknown error')
            print(f"❌ Payment intent creation failed: {error_message}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating payment intent: {e}")
    
    print("\n💡 Summary of Fixes Applied:")
    print("   ✅ Fixed gig.hourly_rate → gig.price_per_session")
    print("   ✅ Fixed gig.title → gig.service_title") 
    print("   ✅ Added automatic_payment_methods with allow_redirects: 'never'")
    print("   ✅ Added return_url fallback for payment confirmation")
    print("   ✅ Added FRONTEND_URL setting")
    print("\n🎯 Expected Behavior:")
    print("   • Payment intent creation should work without attribute errors")
    print("   • Payment confirmation should not require return_url for card payments")
    print("   • Stripe test errors are expected without proper test cards/configuration")

if __name__ == "__main__":
    test_complete_payment_flow()
