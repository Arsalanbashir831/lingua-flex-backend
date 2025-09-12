#!/usr/bin/env python3
"""
Test script to verify the return_url error fix for manual payment confirmation
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_return_url_fix():
    """Test that payment intent creation works without return_url requirement"""
    
    print("🧪 Testing Return URL Error Fix\n")
    
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
    
    # Test the exact request that was failing
    print("\n2️⃣ Testing PaymentIntent creation with payment method...")
    print("   (This was giving return_url error)")
    
    payment_intent_data = {
        "session_booking_id": 56,
        "payment_method_id": "pm_card_visa",
        "save_payment_method": True
    }
    
    try:
        response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data, headers=headers)
        
        print(f"   📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ SUCCESS: PaymentIntent created without return_url error!")
            print(f"   Client Secret: {result.get('client_secret', 'N/A')[:30]}...")
            print(f"   Payment ID: {result.get('payment_id', 'N/A')}")
            print(f"   Amount: ${result.get('amount_dollars', 'N/A')}")
            
            # Test payment confirmation
            client_secret = result.get('client_secret', '')
            if '_secret_' in client_secret:
                payment_intent_id = client_secret.split('_secret_')[0]
                
                print(f"\n   🔄 Testing payment confirmation...")
                print(f"   Payment Intent ID: {payment_intent_id}")
                
                confirm_data = {"payment_intent_id": payment_intent_id}
                
                confirm_response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
                
                print(f"   📊 Confirmation Status: {confirm_response.status_code}")
                
                if confirm_response.status_code == 200:
                    confirm_result = confirm_response.json()
                    print("   ✅ Payment confirmation successful!")
                    print(f"   Payment Status: {confirm_result.get('status')}")
                    print(f"   Requires Action: {confirm_result.get('requires_action')}")
                    
                    if confirm_result.get('status') == 'succeeded':
                        print("   🎉 PAYMENT COMPLETED SUCCESSFULLY!")
                    elif confirm_result.get('status') in ['requires_payment_method', 'requires_confirmation']:
                        print("   ℹ️ Payment needs additional steps (normal for test mode)")
                    else:
                        print(f"   📊 Payment Status: {confirm_result.get('status')}")
                        
                else:
                    error_response = confirm_response.json() if confirm_response.status_code == 400 else {"error": confirm_response.text}
                    error_message = error_response.get('error', 'Unknown error')
                    print(f"   ⚠️ Confirmation issue: {error_message}")
                    
                    if "return_url" in error_message.lower():
                        print("   🚨 RETURN_URL ERROR STILL EXISTS in confirmation!")
                    else:
                        print("   ✅ No return_url errors - different issue")
                        
        else:
            error_response = response.json() if response.status_code == 400 else {"error": response.text}
            error_message = error_response.get('error', 'Unknown error')
            print(f"   ❌ FAILED: {error_message}")
            
            if "return_url" in error_message.lower():
                print("   🚨 RETURN_URL ERROR STILL EXISTS!")
                print("   💡 The fix didn't work - need to check payment_method_types setting")
            elif "automatic_payment_methods, confirmation_method" in error_message:
                print("   🚨 PARAMETER CONFLICT RETURNED!")
                print("   💡 The parameter fix was reverted somehow")
            else:
                print("   ✅ Return_url error fixed, but different error occurred")
                print("   ℹ️ This might be booking-related or Stripe configuration")
                
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
    
    # Test different payment methods to ensure compatibility
    print("\n3️⃣ Testing different test payment methods...")
    
    test_payment_methods = [
        ("pm_card_mastercard", "Mastercard"),
        ("pm_card_amex", "American Express"),
        ("pm_card_decline", "Declined Card (should fail)")
    ]
    
    for pm_id, pm_name in test_payment_methods:
        print(f"\n   Testing {pm_name}: {pm_id}")
        
        test_data = {
            "session_booking_id": 56,
            "payment_method_id": pm_id,
            "save_payment_method": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=test_data, headers=headers)
            
            if response.status_code == 200:
                print(f"   ✅ {pm_name}: PaymentIntent created successfully")
            else:
                error_response = response.json() if response.status_code == 400 else {"error": response.text}
                error_message = error_response.get('error', 'Unknown error')
                
                if "return_url" in error_message.lower():
                    print(f"   ❌ {pm_name}: Return_url error still exists")
                elif "declined" in error_message.lower() and "decline" in pm_id:
                    print(f"   ✅ {pm_name}: Properly declined (expected)")
                else:
                    print(f"   ⚠️ {pm_name}: Different error - {error_message[:50]}...")
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {pm_name}: Request error - {e}")
    
    print("\n💡 Fix Summary:")
    print("   🔧 Added payment_method_types: ['card'] for manual confirmation")
    print("   📋 This restricts to card payments only (no redirect methods)")
    print("   ✅ Should eliminate return_url requirement")
    print("   🎯 Alternative to automatic_payment_methods when using specific payment method")
    
    print("\n🎯 Your Request Should Work Now:")
    print("   POST /api/payments/create-payment-intent/")
    print("   {")
    print('     "session_booking_id": 56,')
    print('     "payment_method_id": "pm_card_visa",')
    print('     "save_payment_method": true')
    print("   }")
    print("   → Should create PaymentIntent without return_url error")

if __name__ == "__main__":
    test_return_url_fix()
