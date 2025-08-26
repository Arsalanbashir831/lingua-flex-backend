#!/usr/bin/env python3
"""
Quick test for the fixed blog creation with thumbnail upload
"""

import requests
import json
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASSWORD = "testpass123"

def create_test_image():
    """Create a small test image"""
    img = Image.new('RGB', (200, 200), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_fixed_upload():
    """Test the fixed thumbnail upload functionality"""
    print("Testing fixed blog creation with thumbnail upload...")
    
    # Step 1: Login
    login_data = {
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/accounts/login/", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    token = response.json().get('token')
    print(f"✅ Login successful")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # Step 2: Test JSON request (should work now)
    print("\nTesting JSON request...")
    json_data = {
        "title": "Test JSON Blog",
        "content": "This is a test blog created with JSON request.",
        "category": 1,
        "tags": ["test", "json"],
        "status": "published"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers={**headers, 'Content-Type': 'application/json'},
        json=json_data
    )
    
    print(f"JSON Request Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ JSON request successful!")
    else:
        print(f"❌ JSON request failed: {response.json()}")
    
    # Step 3: Test form-data with file (should work now)
    print("\nTesting form-data with thumbnail upload...")
    
    test_image = create_test_image()
    
    files = {
        'thumbnail': ('test.jpg', test_image, 'image/jpeg')
    }
    
    data = {
        'title': 'Test Blog with Fixed Upload',
        'content': 'This blog tests the fixed thumbnail upload functionality.',
        'category': 1,
        'tags': '["test", "upload", "fixed"]',
        'status': 'published'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,  # No Content-Type header for form-data
        files=files,
        data=data
    )
    
    print(f"Form-data Request Status: {response.status_code}")
    if response.status_code == 201:
        blog_data = response.json()
        print("✅ Form-data request successful!")
        print(f"📷 Thumbnail URL: {blog_data.get('thumbnail')}")
        
        # Verify the thumbnail URL format
        thumbnail_url = blog_data.get('thumbnail')
        if thumbnail_url and 'supabase' in thumbnail_url and 'blog_thumbnails' in thumbnail_url:
            print("✅ Thumbnail URL format looks correct!")
        else:
            print(f"⚠️ Thumbnail URL format might be incorrect: {thumbnail_url}")
    else:
        print(f"❌ Form-data request failed: {response.json()}")
    
    print("\n" + "="*50)
    print("TESTING COMPLETED")
    print("="*50)

if __name__ == "__main__":
    try:
        test_fixed_upload()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Test error: {e}")
