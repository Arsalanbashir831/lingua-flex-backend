#!/usr/bin/env python3
"""
Test Resend API configuration and email sending
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

import resend
from campaigns.email_service import ResendEmailService

def test_resend_api():
    """Test Resend API configuration"""
    print("🔍 Testing Resend API Configuration...")
    
    try:
        # Check API key
        api_key = settings.RESEND_API_KEY
        if not api_key:
            print("❌ RESEND_API_KEY not found in settings")
            return False
        
        print(f"✅ API Key configured: {api_key[:8]}...")
        
        # Test basic Resend setup
        resend.api_key = api_key
        print("✅ Resend API key set")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Resend API: {e}")
        return False

def test_email_service():
    """Test email service initialization and basic methods"""
    print("\n🔍 Testing Email Service...")
    
    try:
        # Initialize email service
        email_service = ResendEmailService()
        print("✅ Email service initialized")
        
        # Test sending a simple email (to a test email)
        success, email_id, error = email_service.send_single_email(
            recipient_email="test@example.com",  # This will fail but we can see the error
            recipient_name="Test User",
            subject="Test Email",
            content="This is a test email",
            from_name="LinguaFlex",
            from_email="onboarding@lordevs.com"
        )
        
        print(f"📧 Test email result: Success={success}")
        if not success:
            print(f"📧 Error: {error}")
        else:
            print(f"📧 Email ID: {email_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing email service: {e}")
        return False

def test_student_email():
    """Test with a real student email"""
    print("\n🔍 Testing with Real Student Email...")
    
    try:
        from core.models import User
        
        # Get a real student
        student = User.objects.filter(role=User.Role.STUDENT).first()
        if not student:
            print("❌ No students found in database")
            return False
        
        print(f"📧 Testing with student: {student.email}")
        
        # Initialize email service
        email_service = ResendEmailService()
        
        # Test sending email to real student
        success, email_id, error = email_service.send_single_email(
            recipient_email=student.email,
            recipient_name=student.get_full_name(),
            subject="Test Campaign Email from LinguaFlex",
            content="Hello {{student_name}}! This is a test email from your teacher.",
            from_name="LinguaFlex",
            from_email="onboarding@lordevs.com"
        )
        
        print(f"📧 Real email result: Success={success}")
        if not success:
            print(f"📧 Error: {error}")
        else:
            print(f"📧 Email ID: {email_id}")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing real student email: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Resend Email Testing")
    print("=" * 40)
    
    test1 = test_resend_api()
    test2 = test_email_service()
    test3 = test_student_email()
    
    if test1 and test2:
        print("\n✅ Resend API is properly configured!")
        if test3:
            print("✅ Email sending to real students works!")
        else:
            print("⚠️  Email sending to real students failed - check logs above")
    else:
        print("\n❌ Resend API configuration issues found.")
