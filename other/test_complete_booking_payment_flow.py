#!/usr/bin/env python3
"""
Complete Booking and Payment Flow Test Script
Demonstrates the full end-to-end process from booking creation to payment completion
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta

# Add the Django project to the Python path
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')

# Import Django
import django
django.setup()

from core.models import User
from accounts.models import Gig

API_BASE = "http://127.0.0.1:8000/api"

class BookingPaymentFlowTester:
    def __init__(self):
        self.student_token = None
        self.teacher_token = None
        self.booking_id = None
        self.payment_intent_id = None
        self.payment_method_id = None
        
    def login_user(self, email, password):
        """Login and get JWT token"""
        login_url = f"{API_BASE}/login/"
        
        login_data = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(login_url, json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token') or token_data.get('token')
            else:
                print(f"✗ Login failed for {email}: {response.text}")
                return None
        except Exception as e:
            print(f"✗ Login error for {email}: {e}")
            return None
    
    def setup_authentication(self):
        """Setup authentication for both student and teacher"""
        print("🔐 Setting up authentication...")
        
        # Student login
        self.student_token = self.login_user("fahije3853@hostbyt.com", "testpassword1234")
        if not self.student_token:
            raise Exception("Failed to authenticate student")
        print(f"✅ Student authenticated")
        
        # Teacher login  
        self.teacher_token = self.login_user("rebin81412@hostbyt.com", "testpassword123")
        if not self.teacher_token:
            raise Exception("Failed to authenticate teacher")
        print(f"✅ Teacher authenticated")
    
    def get_available_gig(self):
        """Get an available gig for booking"""
        try:
            # Get teacher user to find their gigs
            teacher_user = User.objects.filter(email="rebin81412@hostbyt.com").first()
            if not teacher_user:
                raise Exception("Teacher user not found")
            
            # Look for gigs from this teacher
            gigs = Gig.objects.filter(user_profile__user=teacher_user, is_active=True).first()
            if not gigs:
                raise Exception("No active gigs found for teacher")
            
            print(f"✅ Found gig: {gigs.service_title} (${gigs.price_per_session}/session)")
            return gigs
            
        except Exception as e:
            print(f"✗ Error finding gig: {e}")
            raise
    
    def create_booking(self, gig):
        """Step 1: Student creates a session booking"""
        print(f"\n📅 Step 1: Creating session booking...")
        
        # Calculate future datetime (tomorrow at 2 PM)
        start_time = datetime.now() + timedelta(days=1)
        start_time = start_time.replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1.5)  # 1.5 hour session
        
        booking_data = {
            "teacher": gig.user_profile.user.id,
            "gig": gig.id,
            "start_time": start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "duration_hours": 1.5,
            "scheduled_datetime": start_time.isoformat() + "Z"
        }
        
        headers = {
            "Authorization": f"Bearer {self.student_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{API_BASE}/bookings/bookings/", json=booking_data, headers=headers)
            print(f"📊 Booking creation status: {response.status_code}")
            
            if response.status_code == 201:
                booking = response.json()
                self.booking_id = booking['id']
                print(f"✅ Booking created successfully!")
                print(f"   Booking ID: {self.booking_id}")
                print(f"   Status: {booking.get('status')}")
                print(f"   Payment Status: {booking.get('payment_status')}")
                print(f"   Duration: {booking.get('duration_hours')} hours")
                return booking
            else:
                print(f"✗ Booking creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Booking creation error: {e}")
            return None
    
    def teacher_confirm_booking(self):
        """Step 2: Teacher confirms the booking"""
        print(f"\n✅ Step 2: Teacher confirming booking...")
        
        if not self.booking_id:
            raise Exception("No booking ID available")
        
        headers = {
            "Authorization": f"Bearer {self.teacher_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{API_BASE}/bookings/bookings/{self.booking_id}/confirm/", headers=headers)
            print(f"📊 Confirmation status: {response.status_code}")
            
            if response.status_code == 200:
                booking = response.json()
                print(f"✅ Booking confirmed by teacher!")
                print(f"   Status: {booking.get('status')}")
                print(f"   Payment Status: {booking.get('payment_status')}")
                return booking
            else:
                print(f"✗ Booking confirmation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Booking confirmation error: {e}")
            return None
    
    def add_payment_method(self):
        """Step 3: Student adds a payment method"""
        print(f"\n💳 Step 3: Adding payment method...")
        
        headers = {
            "Authorization": f"Bearer {self.student_token}",
            "Content-Type": "application/json"
        }
        
        payment_method_data = {
            "card_number": "4242424242424242",  # Visa success card
            "exp_month": 12,
            "exp_year": 2026,
            "cvc": "123",
            "cardholder_name": "Test Student",
            "save_for_future": True
        }
        
        try:
            response = requests.post(f"{API_BASE}/payments/add-payment-method/", json=payment_method_data, headers=headers)
            print(f"📊 Payment method status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.payment_method_id = result.get('payment_method_id')
                print(f"✅ Payment method added!")
                print(f"   Payment Method ID: {self.payment_method_id}")
                print(f"   Card: {result.get('card_brand')} ****{result.get('card_last4')}")
                return result
            else:
                print(f"✗ Payment method addition failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Payment method error: {e}")
            return None
    
    def create_payment_intent(self):
        """Step 4: Student creates payment intent"""
        print(f"\n💰 Step 4: Creating payment intent...")
        
        if not self.booking_id:
            raise Exception("No booking ID available")
        
        headers = {
            "Authorization": f"Bearer {self.student_token}",
            "Content-Type": "application/json"
        }
        
        payment_intent_data = {
            "session_booking_id": self.booking_id,
            "payment_method_id": self.payment_method_id,
            "save_payment_method": True
        }
        
        try:
            response = requests.post(f"{API_BASE}/payments/create-payment-intent/", json=payment_intent_data, headers=headers)
            print(f"📊 Payment intent status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.json()
                client_secret = result.get('client_secret', '')
                if '_secret_' in client_secret:
                    self.payment_intent_id = client_secret.split('_secret_')[0]
                
                print(f"✅ Payment intent created!")
                print(f"   Payment ID: {result.get('payment_id')}")
                print(f"   Payment Intent ID: {self.payment_intent_id}")
                print(f"   Amount: ${result.get('amount_dollars')}")
                print(f"   Client Secret: {client_secret[:50]}...")
                return result
            else:
                print(f"✗ Payment intent creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Payment intent error: {e}")
            return None
    
    def confirm_payment(self):
        """Step 5: Student confirms payment"""
        print(f"\n🎯 Step 5: Confirming payment...")
        
        if not self.payment_intent_id or not self.payment_method_id:
            raise Exception("Payment intent ID or payment method ID not available")
        
        headers = {
            "Authorization": f"Bearer {self.student_token}",
            "Content-Type": "application/json"
        }
        
        confirm_data = {
            "payment_intent_id": self.payment_intent_id,
            "payment_method_id": self.payment_method_id
        }
        
        try:
            response = requests.post(f"{API_BASE}/payments/confirm-payment/", json=confirm_data, headers=headers)
            print(f"📊 Payment confirmation status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Payment confirmed successfully!")
                print(f"   Payment Intent ID: {result.get('payment_intent_id')}")
                print(f"   Status: {result.get('status')}")
                print(f"   Amount: ${result.get('amount', 0)/100}")
                print(f"   Currency: {result.get('currency')}")
                return result
            else:
                print(f"✗ Payment confirmation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Payment confirmation error: {e}")
            return None
    
    def verify_final_status(self):
        """Step 6: Verify final booking and payment status"""
        print(f"\n🔍 Step 6: Verifying final status...")
        
        headers = {
            "Authorization": f"Bearer {self.student_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # Check booking status
            response = requests.get(f"{API_BASE}/bookings/bookings/{self.booking_id}/", headers=headers)
            if response.status_code == 200:
                booking = response.json()
                print(f"📋 Final Booking Status:")
                print(f"   ID: {booking.get('id')}")
                print(f"   Status: {booking.get('status')}")
                print(f"   Payment Status: {booking.get('payment_status')}")
                print(f"   Zoom Meeting ID: {booking.get('zoom_meeting_id', 'Not created')}")
                
            # Check payments list
            response = requests.get(f"{API_BASE}/payments/payments/", headers=headers)
            if response.status_code == 200:
                payments = response.json()
                print(f"💰 Payment Records:")
                if isinstance(payments, dict) and 'results' in payments:
                    payments = payments['results']
                
                for payment in payments:
                    if payment.get('session_booking') == self.booking_id:
                        print(f"   Payment ID: {payment.get('id')}")
                        print(f"   Amount: ${payment.get('amount_dollars', 0)}")
                        print(f"   Status: {payment.get('status')}")
                        print(f"   Created: {payment.get('created_at')}")
                        
        except Exception as e:
            print(f"✗ Status verification error: {e}")
    
    def run_complete_flow(self):
        """Execute the complete booking and payment flow"""
        print("🚀 Starting Complete Booking and Payment Flow Test")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_authentication()
            gig = self.get_available_gig()
            
            # Flow steps
            booking = self.create_booking(gig)
            if not booking:
                raise Exception("Failed to create booking")
            
            confirmed_booking = self.teacher_confirm_booking()
            if not confirmed_booking:
                raise Exception("Failed to confirm booking")
            
            payment_method = self.add_payment_method()
            if not payment_method:
                raise Exception("Failed to add payment method")
            
            payment_intent = self.create_payment_intent()
            if not payment_intent:
                raise Exception("Failed to create payment intent")
            
            payment_confirmation = self.confirm_payment()
            if not payment_confirmation:
                raise Exception("Failed to confirm payment")
            
            # Verification
            self.verify_final_status()
            
            print(f"\n🎉 SUCCESS: Complete booking and payment flow executed successfully!")
            print(f"📊 Summary:")
            print(f"   Booking ID: {self.booking_id}")
            print(f"   Payment Intent ID: {self.payment_intent_id}")
            print(f"   Payment Method ID: {self.payment_method_id}")
            
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            print(f"📊 Partial Results:")
            print(f"   Booking ID: {self.booking_id}")
            print(f"   Payment Intent ID: {self.payment_intent_id}")
            print(f"   Payment Method ID: {self.payment_method_id}")

def main():
    tester = BookingPaymentFlowTester()
    tester.run_complete_flow()

if __name__ == "__main__":
    main()
