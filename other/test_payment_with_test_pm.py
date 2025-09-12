#!/usr/bin/env python3
"""
Test adding payment method using Stripe's pre-built test payment methods
This should work without raw card data restrictions
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
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from core.models import User

def get_test_user_credentials():
    """Get existing test user credentials"""
    # Using provided student credentials
    email = "fahije3853@hostbyt.com"
    password = "testpassword1234"
    
    try:
        # Verify user exists in database
        user = User.objects.filter(email=email).first()
        if user:
            print(f"✓ Found test user: {user.email}")
            return email, password
        else:
            print(f"✗ User {email} not found in database")
            return None, None
    except Exception as e:
        print(f"✗ Error checking test user: {e}")
        return None, None

def login_user(email, password):
    """Login and get JWT token"""
    login_url = "http://127.0.0.1:8000/api/login/"
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login Status: {response.status_code}")
        print(f"Login Response: {response.text}")
        
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
    """Test adding a payment method using the endpoint"""
    url = "http://127.0.0.1:8000/api/payments/add-payment-method/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with various Stripe test cards
    test_cards = [
        {
            "name": "Visa Success",
            "card_number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123",
            "cardholder_name": "Test User"
        },
        {
            "name": "Mastercard Success", 
            "card_number": "5555555555554444",
            "exp_month": 10,
            "exp_year": 2026,
            "cvc": "456",
            "cardholder_name": "Test User"
        },
        {
            "name": "Amex Success",
            "card_number": "378282246310005",
            "exp_month": 8,
            "exp_year": 2025,
            "cvc": "1234",
            "cardholder_name": "Test User"
        },
        {
            "name": "Declined Card",
            "card_number": "4000000000000002",
            "exp_month": 6,
            "exp_year": 2025,
            "cvc": "789",
            "cardholder_name": "Test User"
        }
    ]
    
    for card in test_cards:
        print(f"\n🧪 Testing {card['name']}...")
        
        payment_data = {
            "card_number": card["card_number"],
            "exp_month": card["exp_month"],
            "exp_year": card["exp_year"],
            "cvc": card["cvc"],
            "cardholder_name": card["cardholder_name"],
            "save_for_future": True
        }
        
        try:
            response = requests.post(url, headers=headers, json=payment_data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success: {data.get('message')}")
                print(f"  Payment Method ID: {data.get('payment_method_id')}")
                print(f"  Card: {data.get('card_brand')} ending in {data.get('card_last4')}")
                print(f"  Saved: {data.get('saved')}")
            else:
                print(f"✗ Failed: {response.text}")
                
        except Exception as e:
            print(f"✗ Request error: {e}")

def main():
    print("🚀 Testing Payment Method Addition with Pre-built Test Payment Methods")
    print("=" * 70)
    
    # Get test user credentials
    email, password = get_test_user_credentials()
    if not email:
        print("✗ Cannot proceed without test user")
        return
    
    # Login to get token
    print(f"\n🔐 Logging in user: {email}")
    token = login_user(email, password)
    if not token:
        print("✗ Cannot proceed without authentication token")
        return
    
    print(f"✓ Got token: {token[:50]}...")
    
    # Test payment method addition
    print(f"\n💳 Testing payment method addition...")
    test_add_payment_method(token)
    
    print(f"\n✅ Testing complete!")

if __name__ == "__main__":
    main()
