#!/usr/bin/env python3
"""
Test script for auto-completion management command
Creates test data and runs the command to verify functionality
"""
import sys
import os
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from django.utils import timezone
from django.core.management import call_command
from django.db import transaction
from core.models import User, Student, Teacher
from accounts.models import Gig, TeacherProfile, UserProfile
from bookings.models import SessionBooking
from stripe_payments.models import Payment
from decimal import Decimal

class AutoCompleteBookingsTest:
    def __init__(self):
        self.test_users = []
        self.test_bookings = []
        self.test_payments = []
        
    def create_test_data(self):
        """Create test data for the auto-completion command"""
        print("🧪 Creating test data...")
        
        try:
            with transaction.atomic():
                # Create test student
                student_user = User.objects.create(
                    id="test_student_autocomplete_123",
                    email=f"test_student_autocomplete@example.com",
                    first_name="Test",
                    last_name="Student",
                    role="STUDENT"
                )
                student_profile = Student.objects.create(
                    user=student_user,
                    learning_goals="Test learning goals",
                    proficiency_level="BEGINNER",
                    target_languages=["English"]
                )
                
                # Create test teacher
                teacher_user = User.objects.create(
                    id="test_teacher_autocomplete_123",
                    email=f"test_teacher_autocomplete@example.com",
                    first_name="Test",
                    last_name="Teacher",
                    role="TEACHER"
                )
                teacher_profile = Teacher.objects.create(
                    user=teacher_user,
                    bio="Test teacher for auto-completion",
                    teaching_experience=5,
                    teaching_languages=["English"],
                    hourly_rate=Decimal('25.00')
                )
                
                # Create user profile and teacher profile for gig
                teacher_user_profile = UserProfile.objects.create(
                    user=teacher_user,
                    role="TEACHER",
                    bio="Test teacher profile"
                )
                
                teacher_profile_for_gig = TeacherProfile.objects.create(
                    user_profile=teacher_user_profile,
                    qualification="Test qualification",
                    experience_years=5,
                    about="Test teacher"
                )
                
                self.test_users = [student_user, teacher_user]
                
                # Create test gig
                gig = Gig.objects.create(
                    teacher=teacher_profile_for_gig,
                    category='language',
                    service_type='conversation',
                    service_title='Test English Conversation',
                    short_description='Test gig for auto-completion',
                    full_description='Test gig description',
                    price_per_session=Decimal('25.00'),
                    session_duration=60,
                    what_you_provide_in_session='Conversation practice'
                )
                
                # Create bookings in different scenarios
                now = timezone.now()
                
                # Scenario 1: Completed session that should be auto-completed
                past_end_time = now - timedelta(hours=2)
                past_start_time = past_end_time - timedelta(hours=1)
                
                booking1 = SessionBooking.objects.create(
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    start_time=past_start_time,
                    end_time=past_end_time,
                    duration_hours=Decimal('1.0'),
                    status='CONFIRMED',
                    payment_status='PAID'
                )
                
                payment1 = Payment.objects.create(
                    session_booking=booking1,
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    stripe_payment_intent_id=f"pi_test_autocomplete_1_{int(now.timestamp())}",
                    amount_cents=2625,  # $25 + $1.25 platform fee
                    hourly_rate_cents=2500,
                    session_duration_hours=Decimal('1.0'),
                    platform_fee_cents=125,
                    status='COMPLETED',
                    paid_at=past_start_time + timedelta(minutes=5)
                )
                
                # Scenario 2: Session ended but not confirmed (should NOT be auto-completed)
                booking2 = SessionBooking.objects.create(
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    start_time=past_start_time,
                    end_time=past_end_time,
                    duration_hours=Decimal('1.0'),
                    status='PENDING',  # Not confirmed
                    payment_status='PAID'
                )
                
                payment2 = Payment.objects.create(
                    session_booking=booking2,
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    stripe_payment_intent_id=f"pi_test_autocomplete_2_{int(now.timestamp())}",
                    amount_cents=2625,
                    hourly_rate_cents=2500,
                    session_duration_hours=Decimal('1.0'),
                    platform_fee_cents=125,
                    status='COMPLETED',
                    paid_at=past_start_time + timedelta(minutes=5)
                )
                
                # Scenario 3: Confirmed but payment not completed (should NOT be auto-completed)
                booking3 = SessionBooking.objects.create(
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    start_time=past_start_time,
                    end_time=past_end_time,
                    duration_hours=Decimal('1.0'),
                    status='CONFIRMED',
                    payment_status='UNPAID'
                )
                
                payment3 = Payment.objects.create(
                    session_booking=booking3,
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    stripe_payment_intent_id=f"pi_test_autocomplete_3_{int(now.timestamp())}",
                    amount_cents=2625,
                    hourly_rate_cents=2500,
                    session_duration_hours=Decimal('1.0'),
                    platform_fee_cents=125,
                    status='PENDING',  # Payment not completed
                    paid_at=None
                )
                
                # Scenario 4: Future session (should NOT be auto-completed)
                future_start_time = now + timedelta(hours=1)
                future_end_time = now + timedelta(hours=2)
                
                booking4 = SessionBooking.objects.create(
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    start_time=future_start_time,
                    end_time=future_end_time,
                    duration_hours=Decimal('1.0'),
                    status='CONFIRMED',
                    payment_status='PAID'
                )
                
                payment4 = Payment.objects.create(
                    session_booking=booking4,
                    student=student_user,
                    teacher=teacher_user,
                    gig=gig,
                    stripe_payment_intent_id=f"pi_test_autocomplete_4_{int(now.timestamp())}",
                    amount_cents=2625,
                    hourly_rate_cents=2500,
                    session_duration_hours=Decimal('1.0'),
                    platform_fee_cents=125,
                    status='COMPLETED',
                    paid_at=now - timedelta(minutes=30)
                )
                
                self.test_bookings = [booking1, booking2, booking3, booking4]
                self.test_payments = [payment1, payment2, payment3, payment4]
                
                print(f"✅ Created test data:")
                print(f"   - 2 users (student & teacher)")
                print(f"   - 1 gig")
                print(f"   - 4 bookings with different scenarios")
                print(f"   - 4 payments")
                
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            return False
            
        return True
    
    def test_dry_run(self):
        """Test the management command in dry-run mode"""
        print("\n🧪 Testing dry-run mode...")
        
        try:
            call_command('auto_complete_bookings', '--dry-run', '--verbose')
            print("✅ Dry-run completed successfully")
            return True
        except Exception as e:
            print(f"❌ Dry-run failed: {e}")
            return False
    
    def test_actual_run(self):
        """Test the actual management command"""
        print("\n🧪 Testing actual run...")
        
        # Check status before
        print("Status before auto-completion:")
        for i, booking in enumerate(self.test_bookings, 1):
            booking.refresh_from_db()
            print(f"   Booking {i}: {booking.status} (payment: {booking.payment.status})")
        
        try:
            call_command('auto_complete_bookings', '--verbose')
            print("✅ Auto-completion command completed successfully")
        except Exception as e:
            print(f"❌ Auto-completion failed: {e}")
            return False
        
        # Check status after
        print("\nStatus after auto-completion:")
        for i, booking in enumerate(self.test_bookings, 1):
            booking.refresh_from_db()
            print(f"   Booking {i}: {booking.status} (payment: {booking.payment.status})")
        
        # Verify results
        booking1_completed = self.test_bookings[0].status == 'COMPLETED'
        others_unchanged = all(
            booking.status != 'COMPLETED' 
            for booking in self.test_bookings[1:]
        )
        
        if booking1_completed and others_unchanged:
            print("✅ Auto-completion worked correctly!")
            print("   - Booking 1: Auto-completed (✓)")
            print("   - Booking 2: Not confirmed, ignored (✓)")
            print("   - Booking 3: Payment not completed, ignored (✓)")
            print("   - Booking 4: Future session, ignored (✓)")
            return True
        else:
            print("❌ Auto-completion results incorrect")
            return False
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Delete in reverse dependency order
            Payment.objects.filter(id__in=[p.id for p in self.test_payments]).delete()
            SessionBooking.objects.filter(id__in=[b.id for b in self.test_bookings]).delete()
            Gig.objects.filter(teacher__user__email__contains="test_teacher_autocomplete").delete()
            Student.objects.filter(user__email__contains="autocomplete").delete()
            Teacher.objects.filter(user__email__contains="autocomplete").delete()
            User.objects.filter(email__contains="autocomplete").delete()
            
            print("✅ Test data cleaned up successfully")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def run_test(self):
        """Run the complete test"""
        print("🚀 Starting auto-complete bookings test...")
        
        success = True
        
        # Create test data
        if not self.create_test_data():
            return False
        
        try:
            # Test dry-run
            if not self.test_dry_run():
                success = False
            
            # Test actual run
            if not self.test_actual_run():
                success = False
                
        finally:
            # Always cleanup
            self.cleanup()
        
        if success:
            print("\n🎉 All tests passed! Auto-completion management command is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the output above.")
        
        return success

if __name__ == "__main__":
    test = AutoCompleteBookingsTest()
    success = test.run_test()
    sys.exit(0 if success else 1)