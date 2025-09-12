#!/usr/bin/env python3
"""
Test script showing the correct payment flow with payment methods for API testing
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_correct_payment_flow():
    """Test the correct payment flow with payment method for API testing"""
    
    print("🧪 Testing Correct Payment Flow (with Payment Method)\n")
    
    # Step 1: Login as student (assuming account exists)
    print("1️⃣ Logging in as student...")
    login_data = {
        "email": "test_payment_flow@test.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
        if response.status_code == 200:
            student_token = response.json()["access_token"]
            print("✅ Student logged in successfully")
        else:
            print(f"❌ Student login failed: {response.text}")
            print("ℹ️ Create a student account first or use existing credentials")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Error logging in: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Create PaymentIntent WITHOUT payment method (will fail confirmation)
    print("\n2️⃣ Testing PaymentIntent creation WITHOUT payment method...")
    payment_intent_data_no_method = {
        "session_booking_id": 55,
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data_no_method, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PaymentIntent created (for frontend integration)")
            print(f"   Client Secret: {result.get('client_secret')}")
            
            # Try to confirm this (should fail)
            client_secret = result.get('client_secret', '')
            if '_secret_' in client_secret:
                payment_intent_id = client_secret.split('_secret_')[0]
                
                print("\n   🔄 Attempting to confirm without payment method...")
                confirm_data = {"payment_intent_id": payment_intent_id}
                
                confirm_response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
                
                if confirm_response.status_code == 400:
                    error = confirm_response.json().get('error', '')
                    if 'missing a payment method' in error:
                        print("   ❌ Expected failure: Missing payment method")
                        print("   ℹ️ This is normal - frontend would collect payment details")
                    else:
                        print(f"   ❌ Different error: {error}")
                else:
                    print("   ⚠️ Unexpected success - this shouldn't happen without payment method")
        else:
            print(f"❌ PaymentIntent creation failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    
    # Step 3: Create PaymentIntent WITH payment method (for API testing)
    print("\n3️⃣ Testing PaymentIntent creation WITH test payment method...")
    payment_intent_data_with_method = {
        "session_booking_id": 55,
        "payment_method_id": "pm_card_visa",  # Stripe test payment method
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data_with_method, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PaymentIntent created with payment method")
            print(f"   Client Secret: {result.get('client_secret')}")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Amount: ${result.get('amount_dollars')}")
            
            # Try to confirm this (should work)
            client_secret = result.get('client_secret', '')
            if '_secret_' in client_secret:
                payment_intent_id = client_secret.split('_secret_')[0]
                
                print(f"\n   🔄 Attempting to confirm payment intent: {payment_intent_id}")
                confirm_data = {"payment_intent_id": payment_intent_id}
                
                confirm_response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
                
                print(f"   📊 Confirmation Status: {confirm_response.status_code}")
                
                if confirm_response.status_code == 200:
                    confirm_result = confirm_response.json()
                    print("   ✅ Payment confirmation successful!")
                    print(f"   Status: {confirm_result.get('status')}")
                    print(f"   Requires Action: {confirm_result.get('requires_action')}")
                    
                    if confirm_result.get('status') == 'succeeded':
                        print("   🎉 Payment completed successfully!")
                    elif confirm_result.get('status') == 'requires_payment_method':
                        print("   ℹ️ Still requires payment method (check Stripe dashboard)")
                    else:
                        print(f"   ℹ️ Payment status: {confirm_result.get('status')}")
                        
                else:
                    error_response = confirm_response.json() if confirm_response.status_code == 400 else {"error": confirm_response.text}
                    error_message = error_response.get('error', 'Unknown error')
                    print(f"   ❌ Confirmation failed: {error_message}")
        else:
            error_response = response.json() if response.status_code == 400 else {"error": response.text}
            print(f"❌ PaymentIntent creation failed: {error_response.get('error', response.text)}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    
    print("\n💡 Summary:")
    print("   📋 Two Different Flows:")
    print("   1. Without payment_method_id: For frontend integration (Stripe.js)")
    print("   2. With payment_method_id: For direct API testing")
    print("\n   🔧 For API Testing:")
    print("   • Always include payment_method_id in create-payment-intent")
    print("   • Use Stripe test payment methods: pm_card_visa, pm_card_mastercard, etc.")
    print("   • Then confirmation should work")
    print("\n   🌐 For Frontend Integration:")
    print("   • Create PaymentIntent without payment_method_id")
    print("   • Use client_secret with Stripe.js to collect payment")
    print("   • Stripe.js handles confirmation automatically")

if __name__ == "__main__":
    test_correct_payment_flow()
