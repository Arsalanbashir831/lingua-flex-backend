#!/usr/bin/env python3
"""
Postman Test Data Setup Script
Creates necessary test data for the LinguaFlex Blog System Postman collection
"""

import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def setup_test_data():
    """Setup test data for Postman collection testing"""
    print("="*60)
    print("LINGUAFLEX BLOG SYSTEM - POSTMAN TEST SETUP")
    print("="*60)
    
    print("\n📋 SETUP INSTRUCTIONS:")
    print("1. Ensure Django server is running: python manage.py runserver")
    print("2. Create a teacher user account if not exists")
    print("3. Update credentials in Postman collection")
    print("4. Import the collection into Postman")
    print("5. Run tests in the recommended order")
    
    print("\n🔧 REQUIRED ENVIRONMENT VARIABLES:")
    print("- base_url: http://127.0.0.1:8000")
    print("- teacher_token: (auto-set after login)")
    print("- category_id: (auto-set after category creation)")
    print("- blog_id: (auto-set after blog creation)")
    
    print("\n📁 TEST FILES NEEDED:")
    print("- Sample JPEG image (recommended: 800x600, <1MB)")
    print("- Sample PNG image (recommended: 600x400, <500KB)")
    print("- Invalid file (e.g., .txt) for error testing")
    
    print("\n🚀 POSTMAN COLLECTION FEATURES:")
    features = [
        "✅ Authentication & token management",
        "✅ Blog CRUD operations with JSON",
        "✅ Blog creation with file upload (single endpoint)",
        "✅ Blog updates with thumbnail replacement",
        "✅ Search, filter, and pagination",
        "✅ Analytics and statistics",
        "✅ Public blog access (no auth)",
        "✅ Error testing and validation",
        "✅ Legacy two-step upload process",
        "✅ Automatic environment variable management"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print("\n📊 TEST SCENARIOS COVERED:")
    scenarios = [
        "Blog creation (JSON format)",
        "Blog creation with thumbnail upload",
        "Blog updates with new thumbnails",
        "File type validation (JPEG, PNG, WebP, GIF)",
        "File size validation (max 5MB)",
        "Authentication requirements",
        "Search and filtering functionality",
        "Public access without authentication",
        "Analytics and view tracking",
        "Error handling and edge cases"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i:2d}. {scenario}")
    
    print("\n🔍 TESTING WORKFLOW:")
    workflow = [
        "Run 'Teacher Login' to get authentication token",
        "Create blog category for testing",
        "Test blog creation with JSON (no file)",
        "Test blog creation with file upload (recommended)",
        "Test blog updates and thumbnail replacement",
        "Test search, filter, and analytics features",
        "Test public blog access",
        "Validate error handling",
        "Clean up test data"
    ]
    
    for i, step in enumerate(workflow, 1):
        print(f"  {i}. {step}")
    
    print("\n💡 TIPS FOR SUCCESS:")
    tips = [
        "Import collection and set up environment variables",
        "Prepare test images before starting",
        "Run requests in the recommended order",
        "Check response status codes and data",
        "Verify thumbnail URLs are generated correctly",
        "Test both form-data and JSON request types",
        "Use different image formats for thorough testing",
        "Monitor Django console for any server errors"
    ]
    
    for tip in tips:
        print(f"  • {tip}")
    
    print("\n🎯 SUCCESS CRITERIA:")
    print("  ✅ All requests return expected status codes")
    print("  ✅ File uploads generate valid Supabase URLs")
    print("  ✅ Blogs are created and updated successfully")
    print("  ✅ Search and filtering work correctly")
    print("  ✅ Public access functions without authentication")
    print("  ✅ Error responses are clear and helpful")
    
    print("\n" + "="*60)
    print("READY TO TEST WITH POSTMAN!")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/blogs/blogs/", timeout=5)
        if response.status_code in [200, 401]:  # 200 for public, 401 for auth endpoints
            print("✅ Django server is running and accessible")
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server")
        print("   Please run: python manage.py runserver")
    except Exception as e:
        print(f"⚠️ Connection test error: {e}")

def create_sample_test_credentials():
    """Create sample test credentials file"""
    credentials = {
        "teacher_credentials": {
            "email": "teacher@example.com",
            "password": "testpass123",
            "note": "Update these with your actual teacher credentials"
        },
        "api_endpoints": {
            "base_url": "http://127.0.0.1:8000",
            "login": "/api/accounts/login/",
            "blogs": "/api/blogs/teacher/blogs/",
            "public_blogs": "/api/blogs/blogs/",
            "categories": "/api/blogs/categories/"
        },
        "test_data": {
            "sample_blog": {
                "title": "Test Blog Title",
                "content": "This is test content for the blog...",
                "tags": ["test", "education", "sample"],
                "status": "published"
            },
            "sample_category": {
                "name": "Test Category",
                "description": "Category for testing purposes"
            }
        }
    }
    
    with open("postman_test_credentials.json", "w") as f:
        json.dump(credentials, f, indent=2)
    
    print("\n📝 Created 'postman_test_credentials.json' with sample data")
    print("   Update the credentials with your actual test account details")

if __name__ == "__main__":
    setup_test_data()
    create_sample_test_credentials()
    
    print(f"\n📦 FILES CREATED:")
    print(f"  • LinguaFlex_Blog_System_API.postman_collection.json")
    print(f"  • POSTMAN_BLOG_TESTING_GUIDE.md")
    print(f"  • postman_test_credentials.json")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Import collection into Postman")
    print(f"  2. Set up environment variables")
    print(f"  3. Prepare test image files")
    print(f"  4. Follow the testing guide")
    print(f"  5. Run tests in recommended order")
