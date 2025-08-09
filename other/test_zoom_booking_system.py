# test_zoom_booking_system.py
"""
Test script for the Zoom booking system
This script demonstrates the complete booking flow from availability check to Zoom meeting creation
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

def test_teacher_availability_setup():
    """Test setting up teacher availability (Teacher perspective)"""
    
    print("=== Testing Teacher Availability Setup ===\n")
    
    # Teacher creates availability slots
    availability_data = {
        "day_of_week": 1,  # Tuesday
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "is_recurring": True
    }
    
    print("1. Teacher creating availability slot:")
    print(f"POST {BASE_URL}/bookings/availability/")
    print(f"Headers: Authorization: Bearer <teacher_token>")
    print(f"Body: {json.dumps(availability_data, indent=2)}\n")
    
    print("Expected Response (201 Created):")
    expected_response = {
        "id": 1,
        "teacher": "teacher-uuid",
        "teacher_name": "Jane Smith",
        "day_of_week": 1,
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "is_recurring": True,
        "date": None
    }
    print(f"{json.dumps(expected_response, indent=2)}\n")

def test_student_booking_flow():
    """Test the complete student booking flow"""
    
    print("=== Testing Student Booking Flow ===\n")
    
    # Step 1: Check available slots
    teacher_id = "teacher-uuid-here"
    date = "2025-01-15"
    
    print("1. Student checking available slots:")
    print(f"GET {BASE_URL}/bookings/slots/available/?teacher_id={teacher_id}&date={date}&duration=60")
    print(f"Headers: Authorization: Bearer <student_token>\n")
    
    print("Expected Response (200 OK):")
    slots_response = {
        "date": "2025-01-15",
        "teacher_id": teacher_id,
        "available_slots": [
            {
                "start_time": "09:00",
                "end_time": "10:00",
                "datetime_start": "2025-01-15T09:00:00",
                "datetime_end": "2025-01-15T10:00:00"
            },
            {
                "start_time": "10:30",
                "end_time": "11:30",
                "datetime_start": "2025-01-15T10:30:00",
                "datetime_end": "2025-01-15T11:30:00"
            }
        ]
    }
    print(f"{json.dumps(slots_response, indent=2)}\n")
    
    # Step 2: Create booking request
    booking_data = {
        "teacher_id": teacher_id,
        "start_time": "2025-01-15T09:00:00Z",
        "duration": 60,
        "notes": "Looking forward to practicing Spanish conversation"
    }
    
    print("2. Student creating booking request:")
    print(f"POST {BASE_URL}/bookings/bookings/")
    print(f"Headers: Authorization: Bearer <student_token>")
    print(f"Body: {json.dumps(booking_data, indent=2)}\n")
    
    print("Expected Response (201 Created):")
    booking_response = {
        "id": "booking-uuid",
        "student": "student-uuid",
        "teacher": teacher_id,
        "student_name": "John Doe",
        "teacher_name": "Jane Smith",
        "start_time": "2025-01-15T09:00:00Z",
        "end_time": "2025-01-15T10:00:00Z",
        "duration_minutes": 60,
        "status": "PENDING",
        "zoom_meeting_id": None,
        "zoom_join_url": None,
        "notes": "Looking forward to practicing Spanish conversation",
        "can_cancel": True,
        "can_reschedule": True,
        "zoom_info": {
            "meeting_id": None,
            "join_url": None,
            "has_meeting": False
        }
    }
    print(f"{json.dumps(booking_response, indent=2)}\n")

def test_teacher_confirmation_flow():
    """Test teacher confirming booking and creating Zoom meeting"""
    
    print("=== Testing Teacher Confirmation Flow ===\n")
    
    booking_id = "booking-uuid"
    
    print("1. Teacher confirming booking and creating Zoom meeting:")
    print(f"POST {BASE_URL}/bookings/bookings/{booking_id}/confirm/")
    print(f"Headers: Authorization: Bearer <teacher_token>\n")
    
    print("Expected Response (200 OK):")
    confirmation_response = {
        "message": "Booking confirmed and Zoom meeting created",
        "booking": {
            "id": booking_id,
            "status": "CONFIRMED",
            "zoom_meeting_id": "123456789",
            "zoom_join_url": "https://zoom.us/j/123456789",
            "zoom_info": {
                "meeting_id": "123456789",
                "join_url": "https://zoom.us/j/123456789",
                "has_meeting": True
            }
        },
        "zoom_info": {
            "join_url": "https://zoom.us/j/123456789",
            "meeting_id": "123456789",
            "password": "meeting_password"
        }
    }
    print(f"{json.dumps(confirmation_response, indent=2)}\n")

def test_booking_management():
    """Test booking management features"""
    
    print("=== Testing Booking Management ===\n")
    
    booking_id = "booking-uuid"
    
    # Test getting user's bookings
    print("1. Getting user's bookings:")
    print(f"GET {BASE_URL}/bookings/bookings/my/?status=CONFIRMED&role=student")
    print(f"Headers: Authorization: Bearer <student_token>\n")
    
    # Test rescheduling
    reschedule_data = {
        "start_time": "2025-01-16T10:00:00Z",
        "duration": 60
    }
    
    print("2. Rescheduling booking:")
    print(f"POST {BASE_URL}/bookings/bookings/{booking_id}/reschedule/")
    print(f"Headers: Authorization: Bearer <student_token>")
    print(f"Body: {json.dumps(reschedule_data, indent=2)}\n")
    
    # Test cancelling
    cancel_data = {
        "reason": "Schedule conflict"
    }
    
    print("3. Cancelling booking:")
    print(f"POST {BASE_URL}/bookings/bookings/{booking_id}/cancel/")
    print(f"Headers: Authorization: Bearer <student_token>")
    print(f"Body: {json.dumps(cancel_data, indent=2)}\n")

def test_feedback_system():
    """Test session feedback system"""
    
    print("=== Testing Feedback System ===\n")
    
    feedback_data = {
        "booking_id": "booking-uuid",
        "rating": 5,
        "comment": "Excellent session! Very helpful teacher."
    }
    
    print("1. Student providing feedback after completed session:")
    print(f"POST {BASE_URL}/bookings/feedback/")
    print(f"Headers: Authorization: Bearer <student_token>")
    print(f"Body: {json.dumps(feedback_data, indent=2)}\n")
    
    print("Expected Response (201 Created):")
    feedback_response = {
        "id": 1,
        "booking": "booking-uuid",
        "booking_info": {
            "session_date": "2025-01-15T09:00:00Z",
            "teacher_name": "Jane Smith",
            "student_name": "John Doe"
        },
        "rating": 5,
        "comment": "Excellent session! Very helpful teacher.",
        "created_at": "2025-01-15T11:00:00Z",
        "is_from_student": True,
        "reviewer_name": "John Doe"
    }
    print(f"{json.dumps(feedback_response, indent=2)}\n")

def show_complete_workflow():
    """Show the complete workflow from both perspectives"""
    
    print("=== Complete Booking Workflow ===\n")
    
    workflow_steps = [
        {
            "step": 1,
            "actor": "Teacher",
            "action": "Sets up availability slots",
            "endpoint": "POST /api/bookings/availability/"
        },
        {
            "step": 2,
            "actor": "Student",
            "action": "Browses available teachers",
            "endpoint": "GET /api/accounts/teacher/list/"
        },
        {
            "step": 3,
            "actor": "Student",
            "action": "Checks teacher's available slots",
            "endpoint": "GET /api/bookings/slots/available/"
        },
        {
            "step": 4,
            "actor": "Student",
            "action": "Creates booking request",
            "endpoint": "POST /api/bookings/bookings/"
        },
        {
            "step": 5,
            "actor": "Teacher",
            "action": "Reviews pending bookings",
            "endpoint": "GET /api/bookings/bookings/my/?role=teacher&status=PENDING"
        },
        {
            "step": 6,
            "actor": "Teacher",
            "action": "Confirms booking (creates Zoom meeting)",
            "endpoint": "POST /api/bookings/bookings/{id}/confirm/"
        },
        {
            "step": 7,
            "actor": "Both",
            "action": "Receive notification with Zoom link",
            "endpoint": "N/A (automatic)"
        },
        {
            "step": 8,
            "actor": "Both",
            "action": "Join Zoom meeting at scheduled time",
            "endpoint": "N/A (Zoom)"
        },
        {
            "step": 9,
            "actor": "Both",
            "action": "Provide feedback after session",
            "endpoint": "POST /api/bookings/feedback/"
        }
    ]
    
    for step in workflow_steps:
        print(f"Step {step['step']}: {step['actor']} - {step['action']}")
        print(f"  Endpoint: {step['endpoint']}\n")

def show_error_scenarios():
    """Show common error scenarios and responses"""
    
    print("=== Common Error Scenarios ===\n")
    
    error_scenarios = [
        {
            "scenario": "Student tries to book unavailable slot",
            "response": {"error": "Time slot is not available"},
            "status": 400
        },
        {
            "scenario": "Non-teacher tries to confirm booking",
            "response": {"error": "Only the assigned teacher can confirm this booking"},
            "status": 403
        },
        {
            "scenario": "Zoom API credentials not configured",
            "response": {"error": "Error creating Zoom meeting: Zoom API credentials not configured"},
            "status": 500
        },
        {
            "scenario": "Trying to cancel completed session",
            "response": {"error": "Cannot cancel completed or already cancelled sessions"},
            "status": 400
        }
    ]
    
    for scenario in error_scenarios:
        print(f"Scenario: {scenario['scenario']}")
        print(f"Status: {scenario['status']}")
        print(f"Response: {json.dumps(scenario['response'], indent=2)}\n")

if __name__ == "__main__":
    print("LinguaFlex Zoom Booking System Test Documentation\n")
    print("=" * 60)
    
    show_complete_workflow()
    test_teacher_availability_setup()
    test_student_booking_flow()
    test_teacher_confirmation_flow()
    test_booking_management()
    test_feedback_system()
    show_error_scenarios()
    
    print("=== Setup Requirements ===")
    print("1. Configure Zoom API credentials in .env file")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Update URLs in rag_app/urls.py to use enhanced booking system")
    print("4. Test with valid Supabase authentication tokens")
    print("\nRefer to 'Zoom_Booking_API_Documentation.md' for complete API documentation.")
