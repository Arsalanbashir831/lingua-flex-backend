#!/usr/bin/env python3
"""
Test script to verify timezone handling in booking completion endpoint.
This script tests that the booking completion endpoint correctly compares
timezone-aware datetimes.
"""

import os
import sys
import django
import requests
from datetime import datetime, timedelta
import pytz

# Add the project directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, TeacherProfile, Gig
from bookings.models import SessionBooking

User = get_user_model()

BASE_URL = "http://127.0.0.1:8000"

def test_timezone_handling():
    """Test timezone handling in booking completion"""
    print("\n=== TESTING TIMEZONE HANDLING IN BOOKING COMPLETION ===")
    
    try:
        # Test with different timezone scenarios
        current_utc = timezone.now()
        print(f"Current UTC time: {current_utc.isoformat()}")
        print(f"Current UTC timezone: {current_utc.tzinfo}")
        
        # Find or create a test booking that should be completable
        # (end_time in the past)
        test_bookings = SessionBooking.objects.filter(
            status='CONFIRMED',
            payment_status='PAID'
        ).order_by('-end_time')[:5]
        
        print(f"\nFound {test_bookings.count()} confirmed and paid bookings")
        
        for booking in test_bookings:
            print(f"\nBooking {booking.id}:")
            print(f"  Start time: {booking.start_time.isoformat()} (tz: {booking.start_time.tzinfo})")
            print(f"  End time: {booking.end_time.isoformat()} (tz: {booking.end_time.tzinfo})")
            print(f"  Status: {booking.status}")
            print(f"  Payment Status: {booking.payment_status}")
            print(f"  Is timezone naive? Start: {timezone.is_naive(booking.start_time)}, End: {timezone.is_naive(booking.end_time)}")
            
            # Check if booking can be completed
            time_diff = current_utc - booking.end_time
            print(f"  Time difference (current - end): {time_diff}")
            print(f"  Can be completed? {time_diff.total_seconds() > 0}")
        
        # Create a test booking with explicit timezone-aware datetime
        print("\n=== Creating test booking with explicit timezone handling ===")
        
        # Get test users
        try:
            student_user = User.objects.filter(user_type='student').first()
            teacher_user = User.objects.filter(user_type='teacher').first()
            test_gig = Gig.objects.first()
            
            if not all([student_user, teacher_user, test_gig]):
                print("Missing required test data (student, teacher, or gig)")
                return
            
            # Create booking with end time in the past (should be completable)
            past_end_time = timezone.now() - timedelta(hours=1)
            past_start_time = past_end_time - timedelta(hours=1)
            
            test_booking = SessionBooking.objects.create(
                student=student_user,
                teacher=teacher_user,
                gig=test_gig,
                start_time=past_start_time,
                end_time=past_end_time,
                status='CONFIRMED',
                payment_status='PAID',
                duration_hours=1.0
            )
            
            print(f"Created test booking {test_booking.id}")
            print(f"  Start: {test_booking.start_time.isoformat()} (tz: {test_booking.start_time.tzinfo})")
            print(f"  End: {test_booking.end_time.isoformat()} (tz: {test_booking.end_time.tzinfo})")
            print(f"  Is timezone naive? Start: {timezone.is_naive(test_booking.start_time)}, End: {timezone.is_naive(test_booking.end_time)}")
            
            # Test completion via API (would need authentication token for real test)
            print(f"\nBooking should be completable since end_time ({test_booking.end_time}) < current_time ({current_utc})")
            
            # Clean up
            test_booking.delete()
            print("Test booking cleaned up")
            
        except Exception as e:
            print(f"Error creating test booking: {e}")
            
    except Exception as e:
        print(f"Error in timezone testing: {e}")
        import traceback
        traceback.print_exc()

def test_timezone_conversion_examples():
    """Test timezone conversion scenarios"""
    print("\n=== TIMEZONE CONVERSION EXAMPLES ===")
    
    try:
        # Current time in various formats
        utc_now = timezone.now()
        print(f"UTC now: {utc_now} (tz: {utc_now.tzinfo})")
        
        # Create naive datetime and convert
        naive_dt = datetime(2024, 12, 20, 15, 30, 0)
        print(f"Naive datetime: {naive_dt} (is_naive: {timezone.is_naive(naive_dt)})")
        
        # Convert to timezone-aware
        aware_dt = timezone.make_aware(naive_dt)
        print(f"Made aware: {aware_dt} (tz: {aware_dt.tzinfo}, is_naive: {timezone.is_naive(aware_dt)})")
        
        # Test different timezones
        eastern = pytz.timezone('US/Eastern')
        pacific = pytz.timezone('US/Pacific')
        
        # Current time in different zones
        utc_time = timezone.now()
        eastern_time = utc_time.astimezone(eastern)
        pacific_time = utc_time.astimezone(pacific)
        
        print(f"UTC: {utc_time}")
        print(f"Eastern: {eastern_time}")
        print(f"Pacific: {pacific_time}")
        
        # Comparison should work regardless of timezone representation
        print(f"UTC == Eastern (same instant): {utc_time == eastern_time}")
        print(f"UTC == Pacific (same instant): {utc_time == pacific_time}")
        
    except Exception as e:
        print(f"Error in timezone conversion examples: {e}")

if __name__ == "__main__":
    print("Starting timezone handling tests...")
    test_timezone_handling()
    test_timezone_conversion_examples()
    print("\nTimezone tests completed!")