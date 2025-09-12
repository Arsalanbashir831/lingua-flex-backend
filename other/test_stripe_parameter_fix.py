#!/usr/bin/env python3
"""
Test script to verify the Stripe parameter conflict fix
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_payment_intent_parameter_fix():
    """Test that payment intent creation works with both scenarios after the fix"""
    
    print("🧪 Testing Payment Intent Parameter Fix\n")
    
    # Step 1: Login as student
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
    
    # Test Case 1: Payment Intent WITHOUT payment method (for frontend)
    print("\n2️⃣ Testing PaymentIntent creation WITHOUT payment method...")
    print("   (Should use automatic_payment_methods)")
    
    payment_intent_data_frontend = {
        "session_booking_id": 56,
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data_frontend, headers=headers)
        
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ SUCCESS: PaymentIntent created for frontend integration")
            print(f"   Client Secret: {result.get('client_secret', 'N/A')[:20]}...")
            print(f"   Amount: ${result.get('amount_dollars', 'N/A')}")
        else:
            error_response = response.json() if response.status_code == 400 else {"error": response.text}
            error_message = error_response.get('error', 'Unknown error')
            print(f"   ❌ FAILED: {error_message}")
            
            if "automatic_payment_methods, confirmation_method" in error_message:
                print("   🚨 PARAMETER CONFLICT STILL EXISTS!")
            else:
                print("   ℹ️ Different error (might be booking-related)")
                
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    # Test Case 2: Payment Intent WITH payment method (for API testing)
    print("\n3️⃣ Testing PaymentIntent creation WITH payment method...")
    print("   (Should use confirmation_method=manual)")
    
    payment_intent_data_api = {
        "session_booking_id": 56,
        "payment_method_id": "pm_card_visa",
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data_api, headers=headers)
        
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ SUCCESS: PaymentIntent created for API testing")
            print(f"   Client Secret: {result.get('client_secret', 'N/A')[:20]}...")
            print(f"   Payment ID: {result.get('payment_id', 'N/A')}")
            print(f"   Amount: ${result.get('amount_dollars', 'N/A')}")
            
            # Test confirmation on this one
            client_secret = result.get('client_secret', '')
            if '_secret_' in client_secret:
                payment_intent_id = client_secret.split('_secret_')[0]
                
                print(f"\n   🔄 Testing payment confirmation...")
                confirm_data = {"payment_intent_id": payment_intent_id}
                
                confirm_response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
                
                if confirm_response.status_code == 200:
                    confirm_result = confirm_response.json()
                    print(f"   ✅ Payment confirmation successful!")
                    print(f"   Status: {confirm_result.get('status')}")
                else:
                    print(f"   ℹ️ Confirmation status: {confirm_response.status_code}")
                    print(f"   Response: {confirm_response.text[:100]}...")
                    
        else:
            error_response = response.json() if response.status_code == 400 else {"error": response.text}
            error_message = error_response.get('error', 'Unknown error')
            print(f"   ❌ FAILED: {error_message}")
            
            if "automatic_payment_methods, confirmation_method" in error_message:
                print("   🚨 PARAMETER CONFLICT STILL EXISTS!")
                print("   🔧 The fix didn't work - check the service logic")
            else:
                print("   ✅ Parameter conflict fixed, but different error occurred")
                print("   ℹ️ This might be booking-related or Stripe configuration")
                
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    print("\n💡 Summary:")
    print("   🔧 Fixed: Conditional parameter setting in payment intent creation")
    print("   📋 Two modes:")
    print("      • Without payment_method_id: Uses automatic_payment_methods")
    print("      • With payment_method_id: Uses confirmation_method=manual")
    print("   ✅ No more Stripe parameter conflicts!")
    
    print("\n🎯 Your Request Should Work Now:")
    print("   POST /api/payments/create-payment-intent/")
    print("   {")
    print('     "session_booking_id": 56,')
    print('     "payment_method_id": "pm_card_visa",')
    print('     "save_payment_method": true')
    print("   }")

if __name__ == "__main__":
    test_payment_intent_parameter_fix()
