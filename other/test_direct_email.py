#!/usr/bin/env python3
"""
Direct test of email service with debug output
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from campaigns.models import Campaign
from campaigns.email_service import ResendEmailService

def test_specific_email_sending():
    """Test sending to the specific email that's failing"""
    print("🔧 Testing Specific Email Sending with Debug Output")
    print("=" * 60)
    
    try:
        # Get campaign 6
        campaign = Campaign.objects.get(id=6)
        print(f"📋 Campaign: {campaign.title}")
        print(f"📋 Campaign status: {campaign.status}")
        print(f"📋 From name: {campaign.from_name}")
        print(f"📋 From email: {campaign.from_email}")
        
        # Test the specific email that's failing
        student_emails = ["hacib31593@evoxury.com"]
        
        # Initialize email service
        email_service = ResendEmailService()
        
        print(f"\n🔧 Starting email sending process...")
        result = email_service.send_campaign_to_specific_students(campaign, student_emails)
        
        print(f"\n📊 Final Results:")
        print(f"   Success: {result.get('success')}")
        print(f"   Sent count: {result.get('sent_count')}")
        print(f"   Failed count: {result.get('failed_count')}")
        print(f"   Error: {result.get('error')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_specific_email_sending()
