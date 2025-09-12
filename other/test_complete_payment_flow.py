#!/usr/bin/env python3
"""
Test the complete payment flow: add payment method and process payment
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

# Now import Django models
from core.models import User

def login_user():
    """Login and get JWT token"""
    login_url = "http://127.0.0.1:8000/api/login/"
    
    login_data = {
        "email": "fahije3853@hostbyt.com",
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

def test_add_payment_method(token):
    """Add a payment method and return the payment method ID"""
    url = "http://127.0.0.1:8000/api/payments/add-payment-method/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "card_number": "4242424242424242",  # Visa success card
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "Test User",
        "save_for_future": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Payment method added: {data.get('payment_method_id')}")
            return data.get('payment_method_id')
        else:
            print(f"✗ Failed to add payment method: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ Request error: {e}")
        return None

def test_process_payment(token, payment_method_id):
    """Test processing a payment"""
    url = "http://127.0.0.1:8000/api/payments/process-payment/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Mock booking data (you may need to adjust based on your actual booking model)
    payment_data = {
        "payment_method_id": payment_method_id,
        "amount": 50.00,  # $50
        "currency": "usd",
        "description": "Test payment for language lesson",
        "save_payment_method": True,
        # Add any other required fields for your payment flow
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        print(f"Payment Status: {response.status_code}")
        print(f"Payment Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Payment successful!")
            print(f"  Payment Intent ID: {data.get('payment_intent_id')}")
            print(f"  Amount: ${data.get('amount', 0)/100}")
            print(f"  Status: {data.get('status')}")
            return True
        else:
            print(f"✗ Payment failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Payment error: {e}")
        return False

def test_get_saved_payment_methods(token):
    """Test retrieving saved payment methods"""
    url = "http://127.0.0.1:8000/api/payments/payment-methods/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Saved Methods Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                methods = data
            elif isinstance(data, dict):
                methods = data.get('payment_methods', data.get('results', []))
            else:
                methods = []
            
            print(f"✓ Found {len(methods)} saved payment methods:")
            for method in methods:
                default_text = " (Default)" if method.get('is_default') else ""
                card_brand = method.get('card_brand', 'Unknown')
                card_last_four = method.get('card_last_four', method.get('last4', 'XXXX'))
                print(f"  - {card_brand} ****{card_last_four}{default_text}")
            return methods
        else:
            print(f"✗ Failed to get saved methods: {response.text}")
            return []
            
    except Exception as e:
        print(f"✗ Request error: {e}")
        return []

def main():
    print("🚀 Testing Complete Payment Flow")
    print("=" * 50)
    
    # Login
    print("🔐 Logging in...")
    token = login_user()
    if not token:
        print("✗ Cannot proceed without authentication")
        return
    
    print(f"✓ Authenticated successfully")
    
    # Test 1: Add payment method
    print(f"\n💳 Step 1: Adding payment method...")
    payment_method_id = test_add_payment_method(token)
    if not payment_method_id:
        print("✗ Cannot proceed without payment method")
        return
    
    # Test 2: Get saved payment methods
    print(f"\n📋 Step 2: Retrieving saved payment methods...")
    saved_methods = test_get_saved_payment_methods(token)
    
    # Test 3: Process payment (if endpoint exists)
    print(f"\n💰 Step 3: Processing test payment...")
    payment_success = test_process_payment(token, payment_method_id)
    
    if payment_success:
        print(f"\n🎉 Complete payment flow successful!")
    else:
        print(f"\n⚠️  Payment method saving works, but payment processing may need additional setup")
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    main()
