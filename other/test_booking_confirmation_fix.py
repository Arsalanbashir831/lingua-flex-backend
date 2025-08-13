"""
Test script for booking confirmation fix
Tests that confirming a booking multiple times doesn't create new meetings
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
BOOKINGS_URL = f"{BASE_URL}/api/bookings/bookings"

def test_booking_confirmation_fix():
    """Test that confirming a booking multiple times keeps the same meeting ID"""
    
    # Your access tokens here
    teacher_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    booking_id = "YOUR_BOOKING_ID_HERE"  # Replace with actual booking ID
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Booking Confirmation Fix")
    print(f"Booking ID: {booking_id}")
    print("="*60)
    
    # First confirmation
    print("\n1. First booking confirmation...")
    try:
        confirm_url = f"{BOOKINGS_URL}/{booking_id}/confirm/"
        response = requests.post(confirm_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ First confirmation successful!")
            print(f"Message: {data.get('message')}")
            
            booking = data.get('booking', {})
            zoom_info = data.get('zoom_info', {})
            
            first_meeting_id = booking.get('zoom_meeting_id')
            first_join_url = booking.get('zoom_join_url')
            first_start_url = booking.get('zoom_start_url')
            
            print(f"Meeting ID: {first_meeting_id}")
            print(f"Join URL: {first_join_url}")
            print(f"Start URL: {first_start_url}")
            print(f"Status: {booking.get('status')}")
            
            # Second confirmation (should not create new meeting)
            print("\n2. Second booking confirmation (should reuse existing meeting)...")
            
            # First, reset booking to PENDING to test again
            # This would normally not be done, but for testing purposes
            print("   Note: In real scenario, booking would already be CONFIRMED")
            
            response2 = requests.post(confirm_url, headers=headers)
            print(f"Status Code: {response2.status_code}")
            
            if response2.status_code == 200:
                data2 = response2.json()
                print("✅ Second confirmation response received!")
                print(f"Message: {data2.get('message')}")
                
                booking2 = data2.get('booking', {})
                
                second_meeting_id = booking2.get('zoom_meeting_id')
                second_join_url = booking2.get('zoom_join_url')
                second_start_url = booking2.get('zoom_start_url')
                
                print(f"Meeting ID: {second_meeting_id}")
                print(f"Join URL: {second_join_url}")
                print(f"Start URL: {second_start_url}")
                
                # Compare meeting details
                print("\n3. Comparing meeting details...")
                if first_meeting_id == second_meeting_id:
                    print("✅ Meeting ID remained the same - GOOD!")
                else:
                    print("❌ Meeting ID changed - BAD!")
                    print(f"   First: {first_meeting_id}")
                    print(f"   Second: {second_meeting_id}")
                
                if first_join_url == second_join_url:
                    print("✅ Join URL remained the same - GOOD!")
                else:
                    print("❌ Join URL changed - BAD!")
                    print(f"   First: {first_join_url}")
                    print(f"   Second: {second_join_url}")
                
                if first_start_url == second_start_url:
                    print("✅ Start URL remained the same - GOOD!")
                else:
                    print("❌ Start URL changed - BAD!")
                    print(f"   First: {first_start_url}")
                    print(f"   Second: {second_start_url}")
                    
            elif response2.status_code == 400:
                error_data = response2.json()
                if "Only pending bookings can be confirmed" in error_data.get('error', ''):
                    print("✅ Expected behavior: Booking already confirmed, cannot confirm again")
                else:
                    print(f"❌ Unexpected error: {error_data}")
            else:
                print(f"❌ Unexpected status code: {response2.status_code}")
                print(f"Response: {response2.text}")
                
        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Bad Request: {error_data.get('error', 'Unknown error')}")
        elif response.status_code == 403:
            print("❌ Forbidden: Only the assigned teacher can confirm this booking")
        elif response.status_code == 404:
            print("❌ Not Found: Booking not found")
        else:
            print(f"❌ Unexpected error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_booking_status_flow():
    """Test the complete booking status flow"""
    
    teacher_token = "YOUR_TEACHER_ACCESS_TOKEN_HERE"  # Replace with actual teacher token
    booking_id = "YOUR_BOOKING_ID_HERE"  # Replace with actual booking ID
    
    headers = {
        "Authorization": f"Bearer {teacher_token}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "="*60)
    print("Testing Complete Booking Status Flow")
    print("="*60)
    
    # Get current booking details
    print("\n1. Getting current booking details...")
    try:
        get_url = f"{BOOKINGS_URL}/{booking_id}/"
        response = requests.get(get_url, headers=headers)
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Booking retrieved successfully!")
            print(f"Status: {booking.get('status')}")
            print(f"Has meeting ID: {bool(booking.get('zoom_meeting_id'))}")
            print(f"Has join URL: {bool(booking.get('zoom_join_url'))}")
            print(f"Has start URL: {bool(booking.get('zoom_start_url'))}")
            
            if booking.get('zoom_meeting_id'):
                print(f"Meeting ID: {booking.get('zoom_meeting_id')}")
                print(f"Join URL: {booking.get('zoom_join_url')}")
        else:
            print(f"❌ Failed to get booking: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting booking: {e}")

def show_fix_explanation():
    """Show explanation of the fix"""
    
    print("\n" + "="*60)
    print("BOOKING CONFIRMATION FIX EXPLANATION")
    print("="*60)
    
    print("""
🔧 PROBLEM:
   - Every time a teacher confirmed a booking, a NEW Zoom meeting was created
   - This caused the meeting ID and join URL to change
   - Start URL remained the same (which was correct)

✅ SOLUTION:
   1. Before creating a new meeting, check if booking already has a meeting
   2. If meeting exists (zoom_meeting_id and zoom_join_url), just confirm booking status
   3. If no meeting exists, create a new one
   4. Save all Zoom details (meeting_id, join_url, start_url, password)

📋 NEW LOGIC:
   if booking.zoom_meeting_id and booking.zoom_join_url:
       # Meeting exists - just confirm booking
       booking.status = 'CONFIRMED'
       return existing meeting details
   else:
       # No meeting - create new one
       create_new_zoom_meeting()
       save_meeting_details()

🎯 BENEFITS:
   - Meeting links remain stable across multiple confirmations
   - Students can keep the same join URL
   - Teachers keep the same start URL
   - No duplicate meetings created
   - Better user experience
""")

if __name__ == "__main__":
    print("Booking Confirmation Fix Test Suite")
    print("Update the access tokens and booking ID before running")
    print("="*60)
    
    show_fix_explanation()
    
    print("\nTo run tests:")
    print("1. Set valid teacher access token")
    print("2. Set valid booking ID")
    print("3. Ensure Django server is running")
    print("4. Uncomment the test function calls below")
    
    # Uncomment to run actual tests (after setting tokens and booking ID)
    # test_booking_confirmation_fix()
    # test_booking_status_flow()
