#!/usr/bin/env python3
"""
Backend-Only Payment Flow Test Script for LinguaFlex
Tests the complete payment flow without frontend/Stripe.js
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class BackendPaymentTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.jwt_token = None
        self.admin_token = None
        self.teacher_token = None
        
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get JWT token"""
        url = f"{self.base_url}/accounts/login/"
        data = {"email": email, "password": password}
        
        response = self.session.post(url, json=data)
        result = response.json()
        
        if response.status_code == 200 and 'access' in result:
            self.jwt_token = result['access']
            self.session.headers.update({'Authorization': f'Bearer {self.jwt_token}'})
            print(f"✅ Logged in successfully as {email}")
            return result
        else:
            print(f"❌ Login failed: {result}")
            return result
    
    def test_add_payment_method(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test adding a payment method (save card)"""
        url = f"{self.base_url}/stripe-payments/add-payment-method/"
        
        print(f"\n🧪 Testing Add Payment Method")
        print(f"Card: {card_data['card_number']} ({card_data.get('description', 'Unknown')})")
        
        response = self.session.post(url, json=card_data)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ Payment method added successfully")
            print(f"   Payment Method ID: {result.get('payment_method_id')}")
            print(f"   Card Brand: {result.get('card_brand')}")
            print(f"   Last 4: {result.get('card_last4')}")
            print(f"   Saved: {result.get('saved')}")
        else:
            print(f"❌ Failed to add payment method: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                print(f"   Details: {result['details']}")
        
        return result
    
    def test_process_payment_new_card(self, gig_id: int, card_data: Dict[str, Any], save_card: bool = True) -> Dict[str, Any]:
        """Test processing payment with new card"""
        url = f"{self.base_url}/stripe-payments/process-payment/"
        
        payment_data = {
            "gig_id": gig_id,
            "card_details": card_data,
            "save_card": save_card
        }
        
        print(f"\n🧪 Testing Process Payment (New Card)")
        print(f"Gig ID: {gig_id}")
        print(f"Card: {card_data['card_number']} ({card_data.get('description', 'Unknown')})")
        print(f"Save Card: {save_card}")
        
        response = self.session.post(url, json=payment_data)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ Payment processed successfully")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Amount: ${result.get('amount')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Booking ID: {result.get('booking_id')}")
            if result.get('payment_method_saved'):
                print(f"   Card saved for future use")
        else:
            print(f"❌ Payment failed: {result.get('error', 'Unknown error')}")
            if 'details' in result:
                print(f"   Details: {result['details']}")
        
        return result
    
    def test_process_payment_saved_card(self, gig_id: int, payment_method_id: str) -> Dict[str, Any]:
        """Test processing payment with saved card"""
        url = f"{self.base_url}/stripe-payments/process-payment/"
        
        payment_data = {
            "gig_id": gig_id,
            "saved_payment_method_id": payment_method_id
        }
        
        print(f"\n🧪 Testing Process Payment (Saved Card)")
        print(f"Gig ID: {gig_id}")
        print(f"Payment Method ID: {payment_method_id}")
        
        response = self.session.post(url, json=payment_data)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            print(f"✅ Payment processed successfully")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Amount: ${result.get('amount')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Booking ID: {result.get('booking_id')}")
            print(f"   Used Saved Card: {result.get('used_saved_card')}")
        else:
            print(f"❌ Payment failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    def get_saved_payment_methods(self) -> Dict[str, Any]:
        """Get list of saved payment methods"""
        url = f"{self.base_url}/stripe-payments/payment-methods/"
        
        print(f"\n🧪 Getting Saved Payment Methods")
        
        response = self.session.get(url)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            methods = result.get('results', [])
            print(f"✅ Found {len(methods)} saved payment methods")
            for method in methods:
                print(f"   ID: {method.get('stripe_payment_method_id')}")
                print(f"   Brand: {method.get('card_brand')} ending in {method.get('card_last4')}")
                print(f"   Expires: {method.get('card_exp_month')}/{method.get('card_exp_year')}")
        else:
            print(f"❌ Failed to get payment methods: {result}")
        
        return result
    
    def run_comprehensive_test(self):
        """Run comprehensive backend payment flow test"""
        print("🚀 Starting Backend-Only Payment Flow Test")
        print("=" * 60)
        
        # Test cards for different scenarios
        test_cards = [
            {
                "card_number": "4242424242424242",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
                "cardholder_name": "John Doe",
                "description": "Valid Visa Card"
            },
            {
                "card_number": "4000000000000002",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
                "cardholder_name": "Jane Smith",
                "description": "Declined Card"
            },
            {
                "card_number": "4000000000009995",
                "exp_month": 12,
                "exp_year": 2025,
                "cvc": "123",
                "cardholder_name": "Bob Wilson",
                "description": "Insufficient Funds"
            }
        ]
        
        # Test 1: Add valid payment method
        print("\n" + "="*60)
        print("TEST 1: Add Valid Payment Method")
        print("="*60)
        
        valid_card = test_cards[0].copy()
        valid_card["save_for_future"] = True
        add_result = self.test_add_payment_method(valid_card)
        
        # Test 2: Add invalid payment method
        print("\n" + "="*60)
        print("TEST 2: Add Invalid Payment Method (Declined)")
        print("="*60)
        
        invalid_card = test_cards[1].copy()
        invalid_card["save_for_future"] = True
        self.test_add_payment_method(invalid_card)
        
        # Test 3: Get saved payment methods
        print("\n" + "="*60)
        print("TEST 3: Get Saved Payment Methods")
        print("="*60)
        
        methods_result = self.get_saved_payment_methods()
        
        # Extract payment method ID if available
        saved_payment_method_id = None
        if methods_result.get('results'):
            saved_payment_method_id = methods_result['results'][0]['stripe_payment_method_id']
        
        # Test 4: Process payment with new card
        print("\n" + "="*60)
        print("TEST 4: Process Payment with New Card")
        print("="*60)
        
        gig_id = 1  # Assuming test gig exists
        payment_card = test_cards[0].copy()
        del payment_card['description']  # Remove description for API call
        self.test_process_payment_new_card(gig_id, payment_card, save_card=True)
        
        # Test 5: Process payment with saved card (if available)
        if saved_payment_method_id:
            print("\n" + "="*60)
            print("TEST 5: Process Payment with Saved Card")
            print("="*60)
            
            self.test_process_payment_saved_card(gig_id, saved_payment_method_id)
        
        # Test 6: Process payment with declined card
        print("\n" + "="*60)
        print("TEST 6: Process Payment with Declined Card")
        print("="*60)
        
        declined_card = test_cards[1].copy()
        del declined_card['description']
        self.test_process_payment_new_card(gig_id, declined_card, save_card=False)
        
        # Test 7: Process payment with insufficient funds
        print("\n" + "="*60)
        print("TEST 7: Process Payment with Insufficient Funds")
        print("="*60)
        
        insufficient_card = test_cards[2].copy()
        del insufficient_card['description']
        self.test_process_payment_new_card(gig_id, insufficient_card, save_card=False)
        
        print("\n" + "="*60)
        print("🏁 Backend Payment Flow Test Complete")
        print("="*60)


def main():
    """Main test function"""
    tester = BackendPaymentTester()
    
    # Login (you'll need to provide actual test credentials)
    print("Please provide test credentials:")
    email = input("Email: ") or "student@example.com"
    password = input("Password: ") or "testpass123"
    
    login_result = tester.login_user(email, password)
    if not login_result.get('access'):
        print("❌ Cannot proceed without valid login")
        return
    
    # Run comprehensive test
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
