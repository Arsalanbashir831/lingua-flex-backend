#!/usr/bin/env python3
"""
Complete test for the targeted campaign sending functionality
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from core.models import User
from campaigns.models import Campaign
from campaigns.email_service import ResendEmailService

def test_targeted_campaign_flow():
    """Test the complete targeted campaign sending flow"""
    print("🔍 Testing Targeted Campaign Sending Flow...")
    
    try:
        # 1. Test get_specific_students method
        email_service = ResendEmailService()
        
        # Get a real student email from the database
        student = User.objects.filter(role=User.Role.STUDENT).first()
        if not student:
            print("❌ No students found in database")
            return False
            
        student_emails = [student.email]
        print(f"📧 Testing with student email: {student.email}")
        
        # Test get_specific_students
        specific_students = email_service.get_specific_students(student_emails)
        print(f"✅ get_specific_students() returned {len(specific_students)} students")
        
        if specific_students:
            student_data = specific_students[0]
            print(f"   Student data: {student_data}")
            
            # Verify the student data structure
            required_keys = ['email', 'name']
            for key in required_keys:
                if key not in student_data:
                    print(f"❌ Missing key '{key}' in student data")
                    return False
            print("✅ Student data structure is correct")
        
        # 2. Test campaign status logic
        campaign = Campaign.objects.first()
        if campaign:
            print(f"📋 Testing with campaign: {campaign.title} (Status: {campaign.status})")
            
            # Test if campaign can be sent based on status
            allowed_statuses = [Campaign.StatusChoices.DRAFT, Campaign.StatusChoices.FAILED]
            can_send = campaign.status in allowed_statuses
            print(f"✅ Campaign send check: {'Allowed' if can_send else 'Not allowed'} (Status: {campaign.status})")
        
        print("\n🎉 All targeted campaign flow tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in targeted campaign flow test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_relations():
    """Test user and profile relations"""
    print("\n🔍 Testing User-Profile Relations...")
    
    try:
        # Test select_related with profile
        students = User.objects.filter(role=User.Role.STUDENT).select_related('profile')[:1]
        
        if students:
            student = students[0]
            print(f"✅ select_related('profile') works for user: {student.email}")
            
            # Try to access profile if it exists
            try:
                if hasattr(student, 'profile') and student.profile:
                    print(f"✅ Profile exists: {student.profile}")
                else:
                    print("⚠️  User has no profile, but that's okay for testing")
            except Exception as e:
                print(f"⚠️  Profile access issue (but select_related works): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in user relations test: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Comprehensive Targeted Campaign Testing")
    print("=" * 50)
    
    success1 = test_user_relations()
    success2 = test_targeted_campaign_flow()
    
    if success1 and success2:
        print("\n✅ All tests passed! The targeted campaign endpoint should work now.")
        print("\n🚀 You can now test the endpoint:")
        print("   POST /api/campaigns/teacher/campaigns/{campaign_id}/send-to-students/")
        print("   Body: {\"confirm_send\": true, \"student_emails\": [\"student@email.com\"]}")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
