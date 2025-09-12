#!/usr/bin/env python3
"""
Test payment method using API login approach
"""

import requests
import json

def test_with_api_login():
    """Test using the actual API login endpoint"""
    
    base_url = "http://localhost:8000"
    
    # Step 1: Try to login with existing user
    print("🔐 Step 1: Attempting login...")
    
    login_data = {
        "email": "testuser@stripe.com",  # Use the test user we just created
        "password": "testpass123"
    }
    
    login_url = f"{base_url}/api/login/"
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            jwt_token = login_result.get('access')
            
            if jwt_token:
                print(f"✅ Login successful! Token: {jwt_token[:50]}...")
                
                # Step 2: Test payment method endpoint
                print("\n💳 Step 2: Testing payment method endpoint...")
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {jwt_token}"
                }
                
                test_data = {
                    "card_number": "4242424242424242",
                    "exp_month": 12,
                    "exp_year": 2025,
                    "cvc": "123",
                    "cardholder_name": "John Doe",
                    "save_for_future": True
                }
                
                payment_url = f"{base_url}/api/payments/add-payment-method/"
                payment_response = requests.post(payment_url, json=test_data, headers=headers)
                
                print(f"Payment Method Status: {payment_response.status_code}")
                
                try:
                    payment_result = payment_response.json()
                    print(f"Payment Response: {json.dumps(payment_result, indent=2)}")
                    
                    if payment_response.status_code == 200 and payment_result.get('success'):
                        print("\n🎉 SUCCESS! The Stripe raw card issue has been resolved!")
                    else:
                        print(f"\n❌ Still failing: {payment_result.get('error')}")
                        
                except json.JSONDecodeError:
                    print(f"Non-JSON response: {payment_response.text}")
                    
            else:
                print("❌ No access token in login response")
                print(f"Response: {json.dumps(login_result, indent=2)}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            try:
                print(f"Error: {json.dumps(login_response.json(), indent=2)}")
            except:
                print(f"Response: {login_response.text}")
            
            # Try different credentials
            print("\n🔄 Trying different login credentials...")
            
            test_credentials = [
                {"email": "test@example.com", "password": "test123"},
                {"email": "user@example.com", "password": "password"},
                {"email": "student@example.com", "password": "student123"},
            ]
            
            for creds in test_credentials:
                try:
                    resp = requests.post(login_url, json=creds)
                    if resp.status_code == 200:
                        print(f"✅ Found working credentials: {creds['email']}")
                        break
                    else:
                        print(f"❌ {creds['email']}: {resp.status_code}")
                except:
                    continue
                    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_with_api_login()
