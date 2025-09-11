#!/usr/bin/env python3
"""
Quick verification test for the User role fix
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from core.models import User
from campaigns.email_service import ResendEmailService

def test_user_role_access():
    """Test that we can access User.Role.STUDENT without errors"""
    print("🔍 Testing User.Role.STUDENT access...")
    
    try:
        # Test accessing the role
        student_role = User.Role.STUDENT
        print(f"✅ User.Role.STUDENT = {student_role}")
        
        # Test filtering students
        students = User.objects.filter(role=User.Role.STUDENT)
        student_count = students.count()
        print(f"✅ Found {student_count} students in database")
        
        # Test email service methods
        email_service = ResendEmailService()
        
        # Test get_all_students
        all_students = email_service.get_all_students()
        print(f"✅ get_all_students() returned {len(all_students)} students")
        
        # Test get_specific_students with empty list (should work without errors)
        specific_students = email_service.get_specific_students([])
        print(f"✅ get_specific_students([]) returned {len(specific_students)} students")
        
        print("\n🎉 All User.Role.STUDENT references are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 User Role Fix Verification Test")
    print("=" * 50)
    
    success = test_user_role_access()
    
    if success:
        print("\n✅ Fix verified! The targeted campaign endpoint should work now.")
    else:
        print("\n❌ Fix verification failed. Please check the error above.")
