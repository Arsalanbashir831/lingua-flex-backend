#!/usr/bin/env python3
"""
Quick test script for LinguaFlex Stripe Payment API
Run this script to quickly test all endpoints without Postman
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

class LinguaFlexAPITester:
    def __init__(self):
        self.base_url = API_BASE
        self.tokens = {}
        self.test_data = {}
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, headers: Dict = None) -> Dict[str, Any]:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        if headers:
            request_headers.update(headers)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=request_headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            print(f"{method.upper()} {url} - Status: {response.status_code}")
            
            try:
                return {
                    "status_code": response.status_code,
                    "data": response.json(),
                    "success": response.status_code < 400
                }
            except:
                return {
                    "status_code": response.status_code,
                    "data": response.text,
                    "success": response.status_code < 400
                }
                
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def test_authentication(self):
        """Test user registration and login"""
        print("\n🔐 Testing Authentication...")
        
        # Register users
        users = [
            {"email": "student@test.com", "password": "testpass123", "first_name": "Test", "last_name": "Student", "user_type": "student"},
            {"email": "teacher@test.com", "password": "testpass123", "first_name": "Test", "last_name": "Teacher", "user_type": "teacher"}
        ]
        
        for user in users:
            result = self.make_request("POST", "/auth/register/", user)
            print(f"Register {user['user_type']}: {'✅' if result['success'] else '❌'}")
        
        # Login users
        for user in users:
            login_data = {"email": user["email"], "password": user["password"]}
            result = self.make_request("POST", "/auth/login/", login_data)
            
            if result["success"] and "access_token" in result["data"]:
                self.tokens[user["user_type"]] = result["data"]["access_token"]
                print(f"Login {user['user_type']}: ✅ Token obtained")
            else:
                print(f"Login {user['user_type']}: ❌ Failed")
    
    def test_setup_data(self):
        """Create test data (gigs, bookings)"""
        print("\n🎯 Setting up test data...")
        
        if "teacher" not in self.tokens:
            print("❌ Teacher token not available")
            return
        
        # Create teacher profile
        teacher_profile = {
            "bio": "Experienced English teacher",
            "languages": ["English", "Spanish"],
            "teaching_experience": 5,
            "hourly_rate": 25.00,
            "availability": "Flexible hours"
        }
        
        result = self.make_request("POST", "/accounts/teacher-profiles/", teacher_profile, self.tokens["teacher"])
        print(f"Teacher Profile: {'✅' if result['success'] else '❌'}")
        
        # Create gig
        gig_data = {
            "category": "language",
            "service_type": "Language Consultation",
            "service_title": "English Conversation Practice",
            "short_description": "Improve your English speaking skills",
            "full_description": "One-on-one conversation practice",
            "price_per_session": "25.00",
            "session_duration": 60,
            "tags": ["english", "conversation"],
            "what_you_provide_in_session": ["Feedback", "Grammar correction"],
            "status": "active"
        }
        
        result = self.make_request("POST", "/accounts/gigs/", gig_data, self.tokens["teacher"])
        if result["success"]:
            self.test_data["gig_id"] = result["data"].get("id", 1)
            print(f"Gig Creation: ✅ (ID: {self.test_data['gig_id']})")
        else:
            print(f"Gig Creation: ❌")
            self.test_data["gig_id"] = 1  # Fallback
        
        # Create booking
        if "student" not in self.tokens:
            print("❌ Student token not available")
            return
        
        booking_data = {
            "teacher": 2,  # Assuming teacher ID is 2
            "gig": self.test_data["gig_id"],
            "start_time": "2024-12-20T10:00:00Z",
            "end_time": "2024-12-20T11:00:00Z",
            "duration_hours": 1.0,
            "scheduled_datetime": "2024-12-20T10:00:00Z",
            "notes": "Test booking for payment"
        }
        
        result = self.make_request("POST", "/bookings/bookings/", booking_data, self.tokens["student"])
        if result["success"]:
            self.test_data["booking_id"] = result["data"].get("id", 1)
            print(f"Booking Creation: ✅ (ID: {self.test_data['booking_id']})")
        else:
            print(f"Booking Creation: ❌")
            self.test_data["booking_id"] = 1  # Fallback
        
        # Teacher confirms booking
        confirm_url = f"/bookings/bookings/{self.test_data['booking_id']}/confirm/"
        result = self.make_request("POST", confirm_url, {}, self.tokens["teacher"])
        print(f"Booking Confirmation: {'✅' if result['success'] else '❌'}")
    
    def test_payment_system(self):
        """Test payment endpoints"""
        print("\n💳 Testing Payment System...")
        
        if "student" not in self.tokens:
            print("❌ Student token not available")
            return
        
        # Create payment intent
        payment_intent_data = {
            "session_booking_id": self.test_data.get("booking_id", 1),
            "save_payment_method": True
        }
        
        result = self.make_request("POST", "/payments/create-payment-intent/", payment_intent_data, self.tokens["student"])
        if result["success"]:
            self.test_data["payment_id"] = result["data"].get("payment_id")
            print(f"Payment Intent: ✅ (Payment ID: {self.test_data['payment_id']})")
        else:
            print(f"Payment Intent: ❌ - {result.get('data', {}).get('error', 'Unknown error')}")
        
        # List payments
        result = self.make_request("GET", "/payments/payments/", token=self.tokens["student"])
        print(f"List Payments: {'✅' if result['success'] else '❌'}")
        
        # List saved payment methods
        result = self.make_request("GET", "/payments/payment-methods/", token=self.tokens["student"])
        print(f"Payment Methods: {'✅' if result['success'] else '❌'}")
    
    def test_refund_system(self):
        """Test refund endpoints"""
        print("\n🔄 Testing Refund System...")
        
        if "student" not in self.tokens or not self.test_data.get("payment_id"):
            print("❌ Required data not available")
            return
        
        # Create refund request
        refund_data = {
            "payment_id": self.test_data["payment_id"],
            "reason": "Test refund request",
            "requested_amount_dollars": 25.00
        }
        
        result = self.make_request("POST", "/payments/refund-requests/", refund_data, self.tokens["student"])
        if result["success"]:
            self.test_data["refund_id"] = result["data"].get("id")
            print(f"Refund Request: ✅ (ID: {self.test_data['refund_id']})")
        else:
            print(f"Refund Request: ❌")
        
        # List refund requests
        result = self.make_request("GET", "/payments/refund-requests/", token=self.tokens["student"])
        print(f"List Refunds: {'✅' if result['success'] else '❌'}")
    
    def test_error_scenarios(self):
        """Test error handling"""
        print("\n❌ Testing Error Scenarios...")
        
        # Unauthorized access
        result = self.make_request("GET", "/payments/payments/")
        print(f"Unauthorized Access: {'✅' if not result['success'] else '❌'} (Should fail)")
        
        # Invalid booking ID
        invalid_payment_data = {
            "session_booking_id": 999,
            "save_payment_method": True
        }
        
        result = self.make_request("POST", "/payments/create-payment-intent/", invalid_payment_data, self.tokens.get("student"))
        print(f"Invalid Booking: {'✅' if not result['success'] else '❌'} (Should fail)")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting LinguaFlex Stripe Payment API Tests")
        print("=" * 50)
        
        try:
            self.test_authentication()
            time.sleep(1)
            
            self.test_setup_data()
            time.sleep(1)
            
            self.test_payment_system()
            time.sleep(1)
            
            self.test_refund_system()
            time.sleep(1)
            
            self.test_error_scenarios()
            
            print("\n" + "=" * 50)
            print("🎉 Test Suite Complete!")
            print(f"📊 Tokens obtained: {list(self.tokens.keys())}")
            print(f"📋 Test data created: {list(self.test_data.keys())}")
            
        except Exception as e:
            print(f"\n💥 Test suite failed: {e}")

if __name__ == "__main__":
    print("LinguaFlex Stripe Payment API Tester")
    print("Make sure your Django server is running on http://127.0.0.1:8000")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/admin/")
        if response.status_code != 200:
            print("⚠️  Warning: Server might not be running properly")
    except:
        print("❌ Error: Cannot connect to server. Please start Django server first.")
        print("Run: python manage.py runserver")
        exit(1)
    
    tester = LinguaFlexAPITester()
    tester.run_all_tests()
