#!/usr/bin/env python3
"""
Quick test for the backend payment method endpoint
"""

import requests
import json

def test_add_payment_method():
    """Test the add payment method endpoint"""
    
    base_url = "http://localhost:8000"
    
    # Test data - you'll need to replace with actual JWT token
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_JWT_TOKEN_HERE"  # Uncomment and add your token
    }
    
    # Test with Stripe test card
    test_data = {
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "John Doe",
        "save_for_future": True
    }
    
    url = f"{base_url}/api/payments/add-payment-method/"
    
    print("🧪 Testing Add Payment Method Endpoint")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Remove Authorization header for initial test
        test_headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=test_data, headers=test_headers)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("\n✅ Endpoint is working! You need to add a valid JWT token to test the payment flow.")
            print("Steps to test:")
            print("1. Login to get JWT token")
            print("2. Add 'Authorization: Bearer <token>' header") 
            print("3. Run the test again")
        elif response.status_code == 200:
            print("\n✅ Payment method added successfully!")
        else:
            print(f"\n❌ Unexpected response: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_add_payment_method()
