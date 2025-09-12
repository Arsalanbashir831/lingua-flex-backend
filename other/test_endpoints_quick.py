#!/usr/bin/env python3
"""
Quick test to verify payment tracking endpoints are working
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_app.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from stripe_payments.models import Payment
from accounts.models import UserProfile, TeacherProfile
from decimal import Decimal

User = get_user_model()

def test_payment_tracking_endpoints():
    """Quick verification that our payment tracking endpoints are accessible"""
    
    print("🔄 Testing payment tracking endpoints...")
    
    # Create test user
    user = User.objects.create_user(
        email='test_tracking@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        user_type='student',
        is_verified=True
    )
    
    # Create admin user
    admin = User.objects.create_user(
        email='admin_test@example.com',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        user_type='teacher',
        is_staff=True,
        is_superuser=True,
        is_verified=True
    )
    
    # Create tokens
    user_token = Token.objects.create(user=user)
    admin_token = Token.objects.create(user=admin)
    
    # Test API client
    client = APIClient()
    
    print("✅ Test users created")
    
    # Test 1: User payment history (should work even with no payments)
    client.credentials(HTTP_AUTHORIZATION=f'Token {user_token.key}')
    response = client.get('/stripe-payments/history/')
    
    if response.status_code == 200:
        print("✅ User payment history endpoint working")
        data = response.json()
        print(f"   Found {data['summary']['total_payments']} payments")
    else:
        print(f"❌ User payment history failed: {response.status_code}")
        print(f"   Error: {response.content}")
    
    # Test 2: User financial summary
    response = client.get('/stripe-payments/summary/')
    
    if response.status_code == 200:
        print("✅ User financial summary endpoint working")
        data = response.json()
        print(f"   Student spending: ${data['as_student']['total_spent_dollars']}")
        print(f"   Teacher earnings: ${data['as_teacher']['total_earned_dollars']}")
    else:
        print(f"❌ User financial summary failed: {response.status_code}")
    
    # Test 3: Admin payment tracking
    client.credentials(HTTP_AUTHORIZATION=f'Token {admin_token.key}')
    response = client.get('/stripe-payments/admin/tracking/')
    
    if response.status_code == 200:
        print("✅ Admin payment tracking endpoint working")
        data = response.json()
        print(f"   Total revenue: ${data['overview']['total_revenue_dollars']}")
        print(f"   Platform fees: ${data['overview']['platform_fees_earned_dollars']}")
    else:
        print(f"❌ Admin payment tracking failed: {response.status_code}")
        print(f"   Error: {response.content}")
    
    # Test 4: Platform financial report
    response = client.get('/stripe-payments/admin/report/')
    
    if response.status_code == 200:
        print("✅ Platform financial report endpoint working")
        data = response.json()
        print(f"   Current month revenue: ${data['current_month']['revenue_dollars']}")
    else:
        print(f"❌ Platform financial report failed: {response.status_code}")
    
    # Test 5: Payment analytics
    response = client.get('/stripe-payments/admin/analytics/')
    
    if response.status_code == 200:
        print("✅ Payment analytics endpoint working")
        data = response.json()
        print(f"   Unique students: {data['engagement']['unique_students']}")
        print(f"   Unique teachers: {data['engagement']['unique_teachers']}")
    else:
        print(f"❌ Payment analytics failed: {response.status_code}")
    
    print("\n🎉 All endpoint tests completed!")
    
    # Cleanup
    user.delete()
    admin.delete()

if __name__ == "__main__":
    test_payment_tracking_endpoints()
