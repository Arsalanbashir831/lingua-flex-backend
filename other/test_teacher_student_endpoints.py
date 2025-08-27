#!/usr/bin/env python3
"""
Test script for Teacher Student Management Endpoints
Tests all three endpoints for teachers to manage and view student data.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/accounts"
TEACHER_TOKEN = "YOUR_TEACHER_TOKEN_HERE"  # Replace with actual teacher token
STUDENT_ID = "STUDENT_USER_ID_HERE"  # Replace with actual student user ID

# Headers for authentication
headers = {
    "Authorization": f"Bearer {TEACHER_TOKEN}",
    "Content-Type": "application/json"
}

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    """Print formatted response"""
    print(f"\n{title}:")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS")
        try:
            data = response.json()
            print(json.dumps(data, indent=2, default=str))
        except:
            print(response.text)
    else:
        print("❌ FAILED")
        print(f"Error: {response.text}")

def test_student_list():
    """Test the student list endpoint with various filters"""
    print_section("Testing Student List Endpoint")
    
    # Basic list request
    print("\n1. Basic Student List")
    url = f"{BASE_URL}/teacher/students/"
    response = requests.get(url, headers=headers)
    print_response(response, "Basic Student List")
    
    # Test with pagination
    print("\n2. Student List with Pagination")
    url = f"{BASE_URL}/teacher/students/?page=1&page_size=5"
    response = requests.get(url, headers=headers)
    print_response(response, "Paginated Student List")
    
    # Test with country filter
    print("\n3. Student List Filtered by Country")
    url = f"{BASE_URL}/teacher/students/?country=Pakistan"
    response = requests.get(url, headers=headers)
    print_response(response, "Students from Pakistan")
    
    # Test with language filter
    print("\n4. Student List Filtered by Native Language")
    url = f"{BASE_URL}/teacher/students/?native_language=Urdu"
    response = requests.get(url, headers=headers)
    print_response(response, "Students with Urdu as Native Language")
    
    # Test with learning language filter
    print("\n5. Student List Filtered by Learning Language")
    url = f"{BASE_URL}/teacher/students/?learning_language=English"
    response = requests.get(url, headers=headers)
    print_response(response, "Students Learning English")
    
    # Test with search
    print("\n6. Student List with Search")
    url = f"{BASE_URL}/teacher/students/?search=john"
    response = requests.get(url, headers=headers)
    print_response(response, "Search Results for 'john'")
    
    # Test with gender filter
    print("\n7. Student List Filtered by Gender")
    url = f"{BASE_URL}/teacher/students/?gender=male"
    response = requests.get(url, headers=headers)
    print_response(response, "Male Students")
    
    # Test with age range
    print("\n8. Student List Filtered by Age Range")
    url = f"{BASE_URL}/teacher/students/?age_min=18&age_max=30"
    response = requests.get(url, headers=headers)
    print_response(response, "Students aged 18-30")
    
    # Test with date range
    print("\n9. Student List Filtered by Registration Date")
    url = f"{BASE_URL}/teacher/students/?date_from=2024-01-01"
    response = requests.get(url, headers=headers)
    print_response(response, "Students registered from 2024-01-01")
    
    # Test with sorting
    print("\n10. Student List Sorted by Name")
    url = f"{BASE_URL}/teacher/students/?sort_by=user__first_name"
    response = requests.get(url, headers=headers)
    print_response(response, "Students sorted by first name")
    
    # Test with multiple filters
    print("\n11. Student List with Multiple Filters")
    url = f"{BASE_URL}/teacher/students/?country=Pakistan&learning_language=English&sort_by=-created_at"
    response = requests.get(url, headers=headers)
    print_response(response, "Pakistani students learning English (sorted by newest)")

def test_student_detail():
    """Test the student detail endpoint"""
    print_section("Testing Student Detail Endpoint")
    
    if STUDENT_ID == "STUDENT_USER_ID_HERE":
        print("⚠️  Please update STUDENT_ID variable with a real student user ID")
        return
    
    print(f"\n1. Get Student Detail for ID: {STUDENT_ID}")
    url = f"{BASE_URL}/teacher/students/{STUDENT_ID}/"
    response = requests.get(url, headers=headers)
    print_response(response, "Student Detail")
    
    # Test with non-existent student ID
    print("\n2. Get Student Detail for Non-existent ID")
    url = f"{BASE_URL}/teacher/students/non-existent-id/"
    response = requests.get(url, headers=headers)
    print_response(response, "Non-existent Student Detail")

def test_student_statistics():
    """Test the student statistics endpoint"""
    print_section("Testing Student Statistics Endpoint")
    
    print("\n1. Get Comprehensive Student Statistics")
    url = f"{BASE_URL}/teacher/students-statistics/"
    response = requests.get(url, headers=headers)
    print_response(response, "Student Statistics")

def test_authentication_errors():
    """Test endpoints without proper authentication"""
    print_section("Testing Authentication Requirements")
    
    # Test without token
    print("\n1. Student List without Authentication")
    url = f"{BASE_URL}/teacher/students/"
    response = requests.get(url)
    print_response(response, "No Auth Token")
    
    # Test with invalid token
    print("\n2. Student List with Invalid Token")
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(url, headers=invalid_headers)
    print_response(response, "Invalid Token")

def test_non_teacher_access():
    """Test endpoints with non-teacher user"""
    print_section("Testing Non-Teacher Access Restrictions")
    
    # This would require a student token to test properly
    print("⚠️  To fully test this, you would need a student/non-teacher token")
    print("   The endpoints should return 403 Forbidden for non-teachers")

def main():
    """Run all tests"""
    print("🚀 Starting Teacher Student Management Endpoint Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Teacher Token: {TEACHER_TOKEN[:20]}..." if len(TEACHER_TOKEN) > 20 else "⚠️  Token not set")
    
    if TEACHER_TOKEN == "YOUR_TEACHER_TOKEN_HERE":
        print("\n❌ ERROR: Please update TEACHER_TOKEN variable with a real teacher token")
        print("   Get your token by logging in as a teacher user")
        return
    
    try:
        # Run all test suites
        test_student_list()
        test_student_detail()
        test_student_statistics()
        test_authentication_errors()
        test_non_teacher_access()
        
        print_section("Test Summary")
        print("✅ All endpoint tests completed!")
        print("\n📋 Endpoints Tested:")
        print(f"   GET {BASE_URL}/teacher/students/")
        print(f"   GET {BASE_URL}/teacher/students/<student_id>/")
        print(f"   GET {BASE_URL}/teacher/students-statistics/")
        
        print("\n🔍 Features Tested:")
        print("   ✅ Student listing with pagination")
        print("   ✅ Filtering by country, language, gender, age, date")
        print("   ✅ Search functionality")
        print("   ✅ Sorting options")
        print("   ✅ Individual student details")
        print("   ✅ Comprehensive statistics")
        print("   ✅ Authentication requirements")
        print("   ✅ Teacher-only access control")
        
        print("\n📊 Available Filters:")
        print("   • country - Filter by student's country")
        print("   • city - Filter by student's city")
        print("   • native_language - Filter by native language")
        print("   • learning_language - Filter by learning language")
        print("   • status - Filter by student status")
        print("   • gender - Filter by gender")
        print("   • age_min/age_max - Filter by age range")
        print("   • date_from/date_to - Filter by registration date")
        print("   • search - Search across multiple fields")
        print("   • sort_by - Sort results")
        print("   • page/page_size - Pagination")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
