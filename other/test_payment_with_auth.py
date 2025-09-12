#!/usr/bin/env python3
"""
Complete test for payment method addition with authentication
"""

import requests
import json
import django
import os
import sys

# Setup Django environment
sys.path.append('/Users/DELL/Desktop/LingualFlex_7')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

def create_test_user():
    """Create a test user for authentication"""
    try:
        # Delete existing test user if exists
        User.objects.filter(email='testuser@example.com').delete()
        
        # Create new test user
        user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Generate JWT token
        token = AccessToken.for_user(user)
        return str(token)
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        return None

def test_payment_method_with_auth():
    """Test the payment method endpoint with proper authentication"""
    
    print("🔧 Creating test user and generating JWT token...")
    jwt_token = create_test_user()
    
    if not jwt_token:
        print("❌ Failed to create test user")
        return
    
    print(f"✅ JWT Token generated: {jwt_token[:50]}...")
    
    base_url = "http://localhost:8000"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    # Test data
    test_data = {
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "John Doe",
        "save_for_future": True
    }
    
    url = f"{base_url}/api/payments/add-payment-method/"
    
    print("\n🧪 Testing Add Payment Method Endpoint")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers)
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200 and response_json.get('success'):
                print("\n✅ SUCCESS! Payment method added successfully!")
                print(f"   Payment Method ID: {response_json.get('payment_method_id')}")
                print(f"   Card Brand: {response_json.get('card_brand')}")
                print(f"   Last 4: {response_json.get('card_last4')}")
                print(f"   Saved: {response_json.get('saved')}")
            else:
                print(f"\n❌ FAILED: {response_json.get('error', 'Unknown error')}")
                if 'details' in response_json:
                    print(f"   Details: {response_json['details']}")
                    
        except json.JSONDecodeError:
            print(f"Non-JSON Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection failed. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_payment_method_with_auth()
