#!/usr/bin/env python3
"""
Test the complete targeted campaign sending endpoint
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from campaigns.models import Campaign
from campaigns.email_service import ResendEmailService
from core.models import User

def test_targeted_campaign_sending():
    """Test sending a campaign to specific students"""
    print("🔍 Testing Complete Targeted Campaign Sending...")
    
    try:
        # Get a campaign
        campaign = Campaign.objects.first()
        if not campaign:
            print("❌ No campaigns found in database")
            return False
        
        # Get a real student email
        student = User.objects.filter(role=User.Role.STUDENT).first()
        if not student:
            print("❌ No students found in database")
            return False
        
        student_emails = [student.email]
        
        print(f"📋 Campaign: {campaign.title}")
        print(f"📧 Student email: {student.email}")
        print(f"📧 Student name: {student.get_full_name()}")
        print(f"📧 Campaign status: {campaign.status}")
        
        # Initialize email service
        email_service = ResendEmailService()
        
        # Test the complete flow
        result = email_service.send_campaign_to_specific_students(campaign, student_emails)
        
        print(f"\n📊 Campaign Sending Results:")
        print(f"   Success: {result.get('success')}")
        print(f"   Sent count: {result.get('sent_count')}")
        print(f"   Failed count: {result.get('failed_count')}")
        print(f"   Total recipients: {result.get('total_recipients')}")
        print(f"   Missing students: {result.get('missing_students')}")
        
        if result.get('success') and result.get('sent_count') > 0:
            print("✅ Campaign sent successfully!")
            return True
        else:
            print(f"❌ Campaign sending failed: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing targeted campaign sending: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Complete Targeted Campaign Sending Test")
    print("=" * 50)
    
    success = test_targeted_campaign_sending()
    
    if success:
        print("\n✅ Targeted campaign sending is working perfectly!")
        print("🚀 The API endpoint should now work with real email delivery.")
    else:
        print("\n❌ Targeted campaign sending test failed.")
