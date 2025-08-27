#!/usr/bin/env python3
"""
Quick test to verify the get_full_name method works
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from core.models import User

def test_get_full_name():
    """Test the get_full_name method"""
    print("🔍 Testing User.get_full_name() method...")
    
    try:
        # Get a user (any user) to test the method
        user = User.objects.first()
        if user:
            full_name = user.get_full_name()
            print(f"✅ get_full_name() works! User: {user.email}, Full name: '{full_name}'")
            
            # Test the method directly
            print(f"   First name: {user.first_name}")
            print(f"   Last name: {user.last_name}")
            print(f"   Username: {user.username}")
            return True
        else:
            print("❌ No users found in database to test")
            return False
            
    except Exception as e:
        print(f"❌ Error testing get_full_name(): {e}")
        return False

if __name__ == "__main__":
    print("🔧 User get_full_name() Method Test")
    print("=" * 40)
    
    success = test_get_full_name()
    
    if success:
        print("\n✅ get_full_name() method is working correctly!")
    else:
        print("\n❌ get_full_name() method test failed.")
