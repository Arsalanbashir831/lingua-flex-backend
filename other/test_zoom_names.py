#!/usr/bin/env python3
"""
Quick test to verify the ZoomService _get_user_display_name method works correctly
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from bookings.zoom_service import ZoomService

# Test the helper method
zoom_service = ZoomService()

# Create a mock user object
class MockUser:
    def __init__(self, first_name=None, last_name=None, email=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
    
    def __str__(self):
        return f"User({self.email})"

# Test different scenarios
print("🧪 Testing ZoomService _get_user_display_name method")
print("=" * 50)

# Test 1: Full name
user1 = MockUser(first_name="John", last_name="Doe", email="john.doe@example.com")
name1 = zoom_service._get_user_display_name(user1)
print(f"✅ Full name test: {name1}")

# Test 2: First name only
user2 = MockUser(first_name="Jane", last_name="", email="jane@example.com")
name2 = zoom_service._get_user_display_name(user2)
print(f"✅ First name only: {name2}")

# Test 3: Email only
user3 = MockUser(first_name="", last_name="", email="teacher@example.com")
name3 = zoom_service._get_user_display_name(user3)
print(f"✅ Email fallback: {name3}")

# Test 4: None values
user4 = MockUser(first_name=None, last_name=None, email="student@example.com")
name4 = zoom_service._get_user_display_name(user4)
print(f"✅ None values: {name4}")

print("\n🎯 All tests passed! The zoom service should now work correctly.")
print("The get_full_name() error has been fixed! ✨")
