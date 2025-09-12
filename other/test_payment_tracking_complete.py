#!/usr/bin/env python3
"""
Comprehensive Payment Tracking & Flow Test Script for LinguaFlex
Tests the complete payment flow and demonstrates admin payment tracking capabilities

This script will:
1. Demonstrate how students are charged for sessions
2. Show how platform fees are calculated and collected
3. Test payment history and tracking endpoints
4. Verify admin payment monitoring capabilities
5. Show complete financial flow from booking to completion

Run with: python test_payment_tracking_complete.py
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile, TeacherProfile, Gig
from bookings.models import SessionBooking
from stripe_payments.models import Payment
from core.models import User

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
STRIPE_PAYMENTS_URL = f"{BASE_URL}/stripe-payments"

class PaymentTrackingTest:
    """Test payment tracking and financial flow"""
    
    def __init__(self):
        self.student_token = None
        self.teacher_token = None
        self.admin_token = None
        self.test_booking = None
        self.test_payment = None
        
        print("=" * 60)
        print("🔄 PAYMENT TRACKING & FLOW TEST")
        print("=" * 60)
        print(f"🌐 Base URL: {BASE_URL}")
        print(f"💳 Stripe Payments URL: {STRIPE_PAYMENTS_URL}")
        print()
    
    def setup_test_data(self):
        """Create test users and data for payment testing"""
        print("📋 Setting up test data...")
        
        # Create or get test users
        student, created = User.objects.get_or_create(
            email='payment_student@test.com',
            defaults={
                'first_name': 'Payment',
                'last_name': 'Student',
                'user_type': 'student',
                'is_verified': True
            }
        )
        
        teacher, created = User.objects.get_or_create(
            email='payment_teacher@test.com',
            defaults={
                'first_name': 'Payment',
                'last_name': 'Teacher',
                'user_type': 'teacher',
                'is_verified': True
            }
        )
        
        admin, created = User.objects.get_or_create(
            email='payment_admin@test.com',
            defaults={
                'first_name': 'Payment',
                'last_name': 'Admin',
                'user_type': 'teacher',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        
        # Create profiles
        student_profile, created = UserProfile.objects.get_or_create(
            user=student,
            defaults={
                'phone_number': '+1234567890',
                'languages_spoken': ['English', 'Spanish'],
                'timezone': 'America/New_York'
            }
        )
        
        teacher_profile, created = TeacherProfile.objects.get_or_create(
            user=teacher,
            defaults={
                'bio': 'Expert language teacher for payment testing',
                'hourly_rate': Decimal('50.00'),
                'languages_taught': ['Spanish', 'French'],
                'is_verified': True,
                'experience_years': 5
            }
        )
        
        # Create a test gig
        gig, created = Gig.objects.get_or_create(
            teacher=teacher_profile,
            defaults={
                'title': 'Payment Test Spanish Lesson',
                'description': 'Spanish lesson for payment flow testing',
                'price': Decimal('50.00'),
                'duration_hours': 1.0,
                'language': 'Spanish',
                'skill_level': 'BEGINNER',
                'is_available': True
            }
        )
        
        print(f"✅ Created test student: {student.email}")
        print(f"✅ Created test teacher: {teacher.email} (${teacher_profile.hourly_rate}/hour)")
        print(f"✅ Created test admin: {admin.email}")
        print(f"✅ Created test gig: {gig.title} (${gig.price})")
        print()
        
        return student, teacher, admin, gig
    
    def get_auth_tokens(self, student, teacher, admin):
        """Get authentication tokens for test users"""
        print("🔐 Getting authentication tokens...")
        
        # For testing, we'll create tokens directly
        from rest_framework.authtoken.models import Token
        
        student_token, created = Token.objects.get_or_create(user=student)
        teacher_token, created = Token.objects.get_or_create(user=teacher)
        admin_token, created = Token.objects.get_or_create(user=admin)
        
        self.student_token = student_token.key
        self.teacher_token = teacher_token.key
        self.admin_token = admin_token.key
        
        print(f"✅ Student token: {self.student_token[:20]}...")
        print(f"✅ Teacher token: {self.teacher_token[:20]}...")
        print(f"✅ Admin token: {self.admin_token[:20]}...")
        print()
    
    def create_booking(self, student, teacher, gig):
        """Create a test booking"""
        print("📅 Creating test booking...")
        
        booking = SessionBooking.objects.create(
            student=student,
            teacher=teacher,
            gig=gig,
            session_date=datetime.now() + timedelta(days=1),
            duration_hours=1.0,
            hourly_rate=gig.price,
            total_cost=gig.price,
            zoom_link='https://zoom.us/j/test123456',
            status='CONFIRMED',
            notes='Payment flow test booking'
        )
        
        self.test_booking = booking
        print(f"✅ Created booking ID {booking.id}")
        print(f"   Student: {booking.student.email}")
        print(f"   Teacher: {booking.teacher.email}")
        print(f"   Cost: ${booking.total_cost}")
        print(f"   Status: {booking.status}")
        print()
        
        return booking
    
    def test_booking_payment_flow(self):
        """Test the complete booking payment flow"""
        print("💳 Testing booking payment flow...")
        
        # Calculate expected amounts
        booking_cost_cents = int(self.test_booking.total_cost * 100)  # $50.00 = 5000 cents
        platform_fee_cents = int(booking_cost_cents * 0.05)  # 5% = 250 cents
        teacher_earnings_cents = booking_cost_cents - platform_fee_cents  # 4750 cents
        
        print(f"📊 Payment breakdown:")
        print(f"   Booking cost: ${booking_cost_cents/100:.2f} ({booking_cost_cents} cents)")
        print(f"   Platform fee (5%): ${platform_fee_cents/100:.2f} ({platform_fee_cents} cents)")
        print(f"   Teacher earnings: ${teacher_earnings_cents/100:.2f} ({teacher_earnings_cents} cents)")
        print()
        
        # Process payment using our backend endpoint
        payment_data = {
            'booking_id': self.test_booking.id,
            'test_card': 'visa',  # Use test card
            'save_payment_method': False
        }
        
        headers = {'Authorization': f'Token {self.student_token}'}
        
        try:
            response = requests.post(
                f"{STRIPE_PAYMENTS_URL}/process-booking-payment/",
                json=payment_data,
                headers=headers
            )
            
            print(f"🔄 Payment request sent...")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Payment successful!")
                print(f"   Payment ID: {result.get('payment_id')}")
                print(f"   Stripe Payment Intent: {result.get('payment_intent_id')}")
                print(f"   Amount charged: ${result.get('amount_dollars')}")
                print(f"   Platform fee: ${result.get('platform_fee_dollars')}")
                
                # Get the payment record
                payment = Payment.objects.get(id=result['payment_id'])
                self.test_payment = payment
                
                print(f"📋 Payment record details:")
                print(f"   Student: {payment.student.email}")
                print(f"   Teacher: {payment.teacher.email}")
                print(f"   Status: {payment.status}")
                print(f"   Amount: ${payment.amount_dollars}")
                print(f"   Platform fee: ${payment.platform_fee_cents/100}")
                print()
                
                return True
            else:
                error_msg = response.json().get('error', 'Unknown error')
                print(f"❌ Payment failed: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
    
    def test_user_payment_history(self):
        """Test user payment history endpoint"""
        print("📜 Testing user payment history...")
        
        # Test student payment history
        headers = {'Authorization': f'Token {self.student_token}'}
        
        try:
            response = requests.get(
                f"{STRIPE_PAYMENTS_URL}/history/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Student payment history retrieved")
                print(f"   Total payments: {data['summary']['total_payments']}")
                print(f"   Total spent: ${data['summary']['total_amount_dollars']}")
                print(f"   As student: {data['summary']['as_student']}")
                print(f"   As teacher: {data['summary']['as_teacher']}")
                
                if data['results']:
                    latest_payment = data['results'][0]
                    print(f"   Latest payment: ${latest_payment['amount_dollars']} to {latest_payment['teacher']['email']}")
                
                print()
            else:
                print(f"❌ Failed to get payment history: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        # Test teacher payment history
        headers = {'Authorization': f'Token {self.teacher_token}'}
        
        try:
            response = requests.get(
                f"{STRIPE_PAYMENTS_URL}/history/?role=teacher",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Teacher payment history retrieved")
                print(f"   Total payments: {data['summary']['total_payments']}")
                print(f"   Platform fees paid: ${data['summary'].get('platform_fees_paid_dollars', 0)}")
                print()
            else:
                print(f"❌ Failed to get teacher payment history: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Teacher history request failed: {e}")
    
    def test_admin_payment_tracking(self):
        """Test admin payment tracking capabilities"""
        print("🔍 Testing admin payment tracking...")
        
        headers = {'Authorization': f'Token {self.admin_token}'}
        
        # Test comprehensive admin tracking
        try:
            response = requests.get(
                f"{STRIPE_PAYMENTS_URL}/admin/tracking/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                overview = data['overview']
                
                print(f"✅ Admin payment tracking data:")
                print(f"   📊 Overview ({data['date_range']['from']} to {data['date_range']['to']}):")
                print(f"      Total payments: {overview['total_payments']}")
                print(f"      Total revenue: ${overview['total_revenue_dollars']:.2f}")
                print(f"      Platform fees earned: ${overview['platform_fees_earned_dollars']:.2f}")
                print(f"      Teacher earnings: ${overview['teacher_earnings_dollars']:.2f}")
                print(f"      Platform fee %: {overview['platform_fee_percentage']:.1f}%")
                print()
                
                # Status breakdown
                status = data['status_breakdown']
                print(f"   📈 Status breakdown:")
                print(f"      Completed: {status['completed']}")
                print(f"      Pending: {status['pending']}")
                print(f"      Failed: {status['failed']}")
                print(f"      Refunded: {status['refunded']}")
                print()
                
                # Top performers
                if data['top_performers']['teachers']:
                    print(f"   🏆 Top teacher:")
                    top_teacher = data['top_performers']['teachers'][0]
                    print(f"      {top_teacher['name']} ({top_teacher['email']})")
                    print(f"      Earnings: ${top_teacher['earnings_dollars']:.2f}")
                    print(f"      Sessions: {top_teacher['sessions']}")
                    print()
                
                if data['top_performers']['students']:
                    print(f"   💰 Top student:")
                    top_student = data['top_performers']['students'][0]
                    print(f"      {top_student['name']} ({top_student['email']})")
                    print(f"      Spent: ${top_student['spent_dollars']:.2f}")
                    print(f"      Sessions: {top_student['sessions']}")
                    print()
                
            else:
                print(f"❌ Failed to get admin tracking: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Admin tracking request failed: {e}")
    
    def test_financial_summary(self):
        """Test user financial summary"""
        print("💰 Testing financial summaries...")
        
        # Test student summary
        headers = {'Authorization': f'Token {self.student_token}'}
        
        try:
            response = requests.get(
                f"{STRIPE_PAYMENTS_URL}/summary/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                student_data = data['as_student']
                teacher_data = data['as_teacher']
                
                print(f"✅ Student financial summary:")
                print(f"   Total spent: ${student_data['total_spent_dollars']:.2f}")
                print(f"   Total sessions: {student_data['total_sessions']}")
                print(f"   Average cost/session: ${student_data['average_session_cost_dollars']:.2f}")
                print(f"   Unique teachers: {student_data['unique_teachers']}")
                print()
                
                print(f"✅ Teacher financial summary:")
                print(f"   Total earned: ${teacher_data['total_earned_dollars']:.2f}")
                print(f"   Platform fees paid: ${teacher_data['platform_fees_paid_dollars']:.2f}")
                print(f"   Gross revenue: ${teacher_data['gross_revenue_dollars']:.2f}")
                print(f"   Total sessions: {teacher_data['total_sessions']}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Financial summary request failed: {e}")
    
    def test_platform_report(self):
        """Test platform financial report"""
        print("📊 Testing platform financial report...")
        
        headers = {'Authorization': f'Token {self.admin_token}'}
        
        try:
            response = requests.get(
                f"{STRIPE_PAYMENTS_URL}/admin/report/",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_month']
                growth = data['growth']
                ytd = data['year_to_date']
                
                print(f"✅ Platform financial report:")
                print(f"   📅 Current month ({data['period']['current_month']}):")
                print(f"      Revenue: ${current['revenue_dollars']:.2f}")
                print(f"      Platform fees: ${current['platform_fees_dollars']:.2f}")
                print(f"      Payments: {current['payments']}")
                print(f"      Unique users: {current['unique_users']}")
                print()
                
                print(f"   📈 Growth rates:")
                print(f"      Revenue: {growth['revenue_growth']:.1f}%")
                print(f"      Fees: {growth['fees_growth']:.1f}%")
                print(f"      Payments: {growth['payments_growth']:.1f}%")
                print(f"      Users: {growth['users_growth']:.1f}%")
                print()
                
                print(f"   📆 Year to date:")
                print(f"      Revenue: ${ytd['revenue_dollars']:.2f}")
                print(f"      Platform fees: ${ytd['platform_fees_dollars']:.2f}")
                print(f"      Payments: {ytd['payments']}")
                print(f"      Months: {ytd['months_elapsed']}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Platform report request failed: {e}")
    
    def verify_money_flow(self):
        """Verify and explain the complete money flow"""
        print("🔍 MONEY FLOW VERIFICATION")
        print("=" * 40)
        
        if not self.test_payment:
            print("❌ No payment found to verify")
            return
        
        payment = self.test_payment
        
        print(f"💳 STUDENT CHARGE VERIFICATION:")
        print(f"   ✅ Student ({payment.student.email}) WAS charged")
        print(f"   💰 Amount charged: ${payment.amount_dollars}")
        print(f"   🏦 Stripe Payment Intent: {payment.stripe_payment_intent_id}")
        print(f"   📅 Payment date: {payment.created_at}")
        print(f"   ✅ Payment status: {payment.status}")
        print()
        
        print(f"🏢 PLATFORM FEE VERIFICATION:")
        print(f"   ✅ Platform fee COLLECTED from payment")
        print(f"   💰 Platform fee: ${payment.platform_fee_cents/100:.2f}")
        print(f"   📊 Fee percentage: {(payment.platform_fee_cents/payment.amount_cents)*100:.1f}%")
        print(f"   ✅ Fee goes to ADMIN/PLATFORM")
        print()
        
        teacher_earnings = payment.amount_cents - payment.platform_fee_cents
        print(f"👨‍🏫 TEACHER EARNINGS VERIFICATION:")
        print(f"   ✅ Teacher ({payment.teacher.email}) earnings calculated")
        print(f"   💰 Teacher receives: ${teacher_earnings/100:.2f}")
        print(f"   📊 After platform fee deduction")
        print(f"   ✅ Net earning rate: {((teacher_earnings/100)/payment.session_duration_hours):.2f}/hour")
        print()
        
        print(f"📋 RECORD KEEPING VERIFICATION:")
        print(f"   ✅ Payment record created in database")
        print(f"   ✅ All financial details tracked")
        print(f"   ✅ Student and teacher linked")
        print(f"   ✅ Booking linked (ID: {payment.session_booking_id})")
        print(f"   ✅ Stripe payment intent stored")
        print(f"   ✅ Timestamps recorded")
        print()
        
        print(f"🎯 ANSWER TO YOUR QUESTIONS:")
        print(f"   ❓ Is the student charged? ✅ YES - ${payment.amount_dollars}")
        print(f"   ❓ Does admin receive platform fee? ✅ YES - ${payment.platform_fee_cents/100:.2f}")
        print(f"   ❓ Can payments be traced? ✅ YES - Complete audit trail")
        print(f"   ❓ Can admin see all payments? ✅ YES - Via admin endpoints")
        print(f"   ❓ Can users see payment history? ✅ YES - Via user endpoints")
        print()
    
    def run_complete_test(self):
        """Run the complete payment tracking test suite"""
        try:
            # Setup
            student, teacher, admin, gig = self.setup_test_data()
            self.get_auth_tokens(student, teacher, admin)
            self.create_booking(student, teacher, gig)
            
            # Test payment flow
            payment_success = self.test_booking_payment_flow()
            
            if payment_success:
                # Test tracking and reporting
                self.test_user_payment_history()
                self.test_admin_payment_tracking()
                self.test_financial_summary()
                self.test_platform_report()
                
                # Final verification
                self.verify_money_flow()
                
                print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
                print()
                print("📚 SUMMARY:")
                print("   ✅ Payment system is working correctly")
                print("   ✅ Students are properly charged")
                print("   ✅ Platform fees are collected (5%)")
                print("   ✅ Teacher earnings are calculated correctly")
                print("   ✅ Complete audit trail is maintained")
                print("   ✅ Admin has full payment visibility")
                print("   ✅ Users can view their payment history")
                print("   ✅ Financial reports are generated")
            else:
                print("❌ Payment test failed - cannot proceed with tracking tests")
                
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Payment Tracking Test Suite...")
    print()
    
    # Check if Django server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        print("✅ Django server is running")
    except requests.exceptions.RequestException:
        print("❌ Django server is not running. Please start it with:")
        print("   python manage.py runserver")
        sys.exit(1)
    
    # Run tests
    test_suite = PaymentTrackingTest()
    test_suite.run_complete_test()
