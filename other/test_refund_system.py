#!/usr/bin/env python3
"""
Test script for the enhanced refund system
Tests both automatic and manual refund flows
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
STUDENT_TOKEN = ""  # Will be filled after login
ADMIN_TOKEN = ""    # Will be filled after admin login

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    """Pretty print response"""
    print(f"\n{title}:")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def test_student_login():
    """Test student login"""
    print_section("1. STUDENT LOGIN")
    
    login_data = {
        "email": "student@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    print_response(response, "Student Login")
    
    if response.status_code == 200:
        global STUDENT_TOKEN
        STUDENT_TOKEN = response.json().get('access_token')
        print(f"Student Token: {STUDENT_TOKEN[:20]}...")
    
    return response.status_code == 200

def test_admin_login():
    """Test admin login"""
    print_section("2. ADMIN LOGIN")
    
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/accounts/login/", json=login_data)
    print_response(response, "Admin Login")
    
    if response.status_code == 200:
        global ADMIN_TOKEN
        ADMIN_TOKEN = response.json().get('access_token')
        print(f"Admin Token: {ADMIN_TOKEN[:20]}...")
    
    return response.status_code == 200

def test_refund_status_check():
    """Test checking refund status for a payment"""
    print_section("3. CHECK REFUND STATUS")
    
    # Use the payment ID from your successful payment (payment_id: 2)
    payment_id = 2
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.get(f"{BASE_URL}/payments/refund/status/{payment_id}/", headers=headers)
    
    print_response(response, "Refund Status Check")
    return response.json() if response.status_code == 200 else None

def test_automatic_refund_request():
    """Test requesting refund for incomplete session (automatic)"""
    print_section("4. REQUEST AUTOMATIC REFUND")
    
    # First, let's create a booking that's not completed to test automatic refund
    # For now, we'll test with the existing payment_id: 2
    
    refund_data = {
        "payment_id": 2,
        "reason": "Student couldn't attend the session",
        "requested_amount_dollars": 13.125  # Full amount
    }
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.post(f"{BASE_URL}/payments/refund/request/", json=refund_data, headers=headers)
    
    print_response(response, "Automatic Refund Request")
    return response.json() if response.status_code == 200 else None

def test_manual_refund_request():
    """Test requesting refund for completed session (manual review)"""
    print_section("5. REQUEST MANUAL REVIEW REFUND")
    
    # This would be for a completed session
    refund_data = {
        "payment_id": 2,  # Assuming this session is completed
        "reason": "Session quality was poor, teacher didn't show up on time",
        "requested_amount_dollars": 10.00  # Partial refund
    }
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.post(f"{BASE_URL}/payments/refund/request/", json=refund_data, headers=headers)
    
    print_response(response, "Manual Review Refund Request")
    return response.json() if response.status_code == 200 else None

def test_student_refund_history():
    """Test getting student's refund history"""
    print_section("6. STUDENT REFUND HISTORY")
    
    headers = {"Authorization": f"Bearer {STUDENT_TOKEN}"}
    response = requests.get(f"{BASE_URL}/payments/refund/request/", headers=headers)
    
    print_response(response, "Student Refund History")
    return response.json() if response.status_code == 200 else None

def test_admin_refund_management():
    """Test admin viewing pending refund requests"""
    print_section("7. ADMIN REFUND MANAGEMENT")
    
    if not ADMIN_TOKEN:
        print("⚠️  Admin token not available. Skipping admin tests.")
        return None
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.get(f"{BASE_URL}/payments/admin/refund/manage/?status=PENDING", headers=headers)
    
    print_response(response, "Admin Pending Refunds")
    return response.json() if response.status_code == 200 else None

def test_admin_approve_refund():
    """Test admin approving a refund"""
    print_section("8. ADMIN APPROVE REFUND")
    
    if not ADMIN_TOKEN:
        print("⚠️  Admin token not available. Skipping admin approval test.")
        return None
    
    # You would get this refund_request_id from the previous step
    approve_data = {
        "refund_request_id": 1,  # Replace with actual ID
        "action": "approve",
        "admin_notes": "Approved - valid reason for refund"
    }
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.post(f"{BASE_URL}/payments/admin/refund/manage/", json=approve_data, headers=headers)
    
    print_response(response, "Admin Refund Approval")
    return response.json() if response.status_code == 200 else None

def test_admin_reject_refund():
    """Test admin rejecting a refund"""
    print_section("9. ADMIN REJECT REFUND")
    
    if not ADMIN_TOKEN:
        print("⚠️  Admin token not available. Skipping admin rejection test.")
        return None
    
    reject_data = {
        "refund_request_id": 2,  # Replace with actual ID
        "action": "reject",
        "admin_notes": "Rejected - session was completed successfully according to teacher feedback"
    }
    
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
    response = requests.post(f"{BASE_URL}/payments/admin/refund/manage/", json=reject_data, headers=headers)
    
    print_response(response, "Admin Refund Rejection")
    return response.json() if response.status_code == 200 else None

def main():
    """Run all refund system tests"""
    print("🔄 Testing Enhanced Refund System")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Test login first
    student_logged_in = test_student_login()
    admin_logged_in = test_admin_login()
    
    if not student_logged_in:
        print("❌ Student login failed. Cannot continue tests.")
        return
    
    # Test refund functionality
    test_refund_status_check()
    test_automatic_refund_request()
    test_manual_refund_request()
    test_student_refund_history()
    
    # Admin tests (if admin login successful)
    if admin_logged_in:
        test_admin_refund_management()
        test_admin_approve_refund()
        test_admin_reject_refund()
    
    print_section("REFUND SYSTEM TEST SUMMARY")
    print("✅ Enhanced refund system endpoints tested")
    print("📋 Key Features Tested:")
    print("  • Automatic refunds for incomplete sessions")
    print("  • Manual review for completed sessions")
    print("  • Student refund request submission")
    print("  • Student refund history viewing")
    print("  • Admin refund management and approval")
    print("  • Refund status checking")
    
    print(f"\n🏁 Test completed at: {datetime.now()}")

if __name__ == "__main__":
    main()
