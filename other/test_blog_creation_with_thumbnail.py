#!/usr/bin/env python3
"""
Blog Creation with Thumbnail Upload Test Script
Tests the updated blog creation endpoint that supports file uploads in a single request
"""

import requests
import json
import os
from io import BytesIO
from PIL import Image

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASSWORD = "testpass123"

def create_test_image(filename="test_thumbnail.jpg", size=(800, 600), format="JPEG"):
    """Create a test image file"""
    img = Image.new('RGB', size, color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes

def test_blog_creation_with_thumbnail():
    """Test blog creation with thumbnail upload in single request"""
    print("="*70)
    print("BLOG CREATION WITH THUMBNAIL UPLOAD TEST")
    print("="*70)
    
    # Step 1: Get authentication token
    print("\n1. Getting authentication token...")
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
    print(f"✅ Login successful, token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Token {token}'
    }
    
    # Step 2: Create blog category first
    print("\n2. Creating blog category...")
    category_data = {
        "name": "Test Category",
        "description": "Category for testing"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/categories/",
        headers=headers,
        json=category_data
    )
    
    if response.status_code == 201:
        category_id = response.json().get('id')
        print(f"✅ Category created with ID: {category_id}")
    else:
        # Try to get existing category
        response = requests.get(f"{BASE_URL}/api/blogs/categories/", headers=headers)
        if response.status_code == 200 and response.json().get('results'):
            category_id = response.json()['results'][0]['id']
            print(f"✅ Using existing category with ID: {category_id}")
        else:
            print("❌ Failed to create or get category")
            return
    
    # Step 3: Test blog creation with thumbnail file
    print("\n3. Testing blog creation with thumbnail file...")
    
    # Create test image
    test_image = create_test_image("blog_thumb.jpg", (800, 600), "JPEG")
    
    # Prepare form data
    files = {
        'thumbnail': ('blog_thumbnail.jpg', test_image, 'image/jpeg')
    }
    
    data = {
        'title': 'Test Blog with File Upload',
        'content': 'This blog was created with a thumbnail file uploaded in the same request!',
        'category': category_id,
        'tags': '["test", "upload", "file", "thumbnail"]',
        'status': 'published',
        'meta_description': 'Test blog for file upload functionality'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Blog Creation Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Blog created successfully with uploaded thumbnail!")
        blog_data = response.json()
        blog_id = blog_data.get('id')
        thumbnail_url = blog_data.get('thumbnail')
        print(f"📝 Blog ID: {blog_id}")
        print(f"📷 Thumbnail URL: {thumbnail_url}")
        created_blog_id = blog_id
    else:
        print("❌ Blog creation failed!")
        return
    
    # Step 4: Test blog creation without thumbnail (optional)
    print("\n4. Testing blog creation without thumbnail...")
    
    data_no_thumb = {
        'title': 'Test Blog without Thumbnail',
        'content': 'This blog was created without a thumbnail file.',
        'category': category_id,
        'tags': '["test", "no-thumbnail"]',
        'status': 'draft'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        data=data_no_thumb
    )
    
    print(f"Blog Creation (No Thumb) Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Blog created successfully without thumbnail!")
    else:
        print(f"❌ Blog creation failed: {response.json()}")
    
    # Step 5: Test blog update with new thumbnail
    print("\n5. Testing blog update with new thumbnail...")
    
    # Create new test image
    test_image_update = create_test_image("updated_thumb.png", (600, 400), "PNG")
    
    files_update = {
        'thumbnail': ('updated_thumbnail.png', test_image_update, 'image/png')
    }
    
    data_update = {
        'title': 'Updated Blog with New Thumbnail',
        'content': 'This blog was updated with a new thumbnail!',
        'status': 'published'
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{created_blog_id}/",
        headers=headers,
        files=files_update,
        data=data_update
    )
    
    print(f"Blog Update Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Blog updated successfully with new thumbnail!")
        updated_blog = response.json()
        print(f"📷 New Thumbnail URL: {updated_blog.get('thumbnail')}")
    else:
        print(f"❌ Blog update failed: {response.json()}")
    
    # Step 6: Test invalid file type
    print("\n6. Testing invalid file type...")
    
    fake_image = BytesIO(b"This is not an image file")
    files_invalid = {
        'thumbnail': ('fake_image.txt', fake_image, 'text/plain')
    }
    
    data_invalid = {
        'title': 'Blog with Invalid File',
        'content': 'This should fail due to invalid file type.',
        'category': category_id,
        'status': 'draft'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        files=files_invalid,
        data=data_invalid
    )
    
    print(f"Invalid File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ File type validation working!")
        print(f"Error: {response.json().get('error')}")
    else:
        print("⚠️ File type validation might not be working properly")
    
    # Step 7: Test large file
    print("\n7. Testing large file size...")
    
    large_image = create_test_image("large_thumb.jpg", (4000, 3000), "JPEG")
    files_large = {
        'thumbnail': ('large_thumbnail.jpg', large_image, 'image/jpeg')
    }
    
    data_large = {
        'title': 'Blog with Large File',
        'content': 'This should fail due to large file size.',
        'category': category_id,
        'status': 'draft'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        files=files_large,
        data=data_large
    )
    
    print(f"Large File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ File size validation working!")
        print(f"Error: {response.json().get('error')}")
    else:
        print("⚠️ File size validation might not be working properly")
    
    # Step 8: Test different image formats
    print("\n8. Testing different image formats...")
    
    formats = [("PNG", "image/png"), ("WEBP", "image/webp")]
    
    for fmt, content_type in formats:
        test_img = create_test_image(f"test.{fmt.lower()}", (400, 300), fmt)
        files_fmt = {
            'thumbnail': (f'test_thumbnail.{fmt.lower()}', test_img, content_type)
        }
        
        data_fmt = {
            'title': f'Blog with {fmt} Thumbnail',
            'content': f'This blog uses a {fmt} thumbnail.',
            'category': category_id,
            'status': 'draft'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/blogs/teacher/blogs/",
            headers=headers,
            files=files_fmt,
            data=data_fmt
        )
        
        if response.status_code == 201:
            print(f"✅ {fmt} format upload successful!")
        else:
            print(f"❌ {fmt} format upload failed: {response.json()}")
    
    print("\n" + "="*70)
    print("BLOG CREATION WITH THUMBNAIL UPLOAD TESTS COMPLETED")
    print("="*70)

def print_postman_guide():
    """Print guide for testing with Postman"""
    print("\n" + "="*70)
    print("POSTMAN TESTING GUIDE - BLOG CREATION WITH THUMBNAIL")
    print("="*70)
    
    print("""
📋 POSTMAN SETUP FOR BLOG CREATION WITH THUMBNAIL:

1. CREATE NEW REQUEST:
   - Method: POST
   - URL: http://127.0.0.1:8000/api/blogs/teacher/blogs/

2. HEADERS:
   - Authorization: Token YOUR_TOKEN_HERE

3. BODY (select "form-data"):
   - title: "My Blog Title" (Text)
   - content: "Blog content here..." (Text)
   - thumbnail: Select image file (File) - OPTIONAL
   - category: 1 (Text)
   - tags: ["tag1", "tag2"] (Text)
   - status: "published" (Text)
   - meta_description: "SEO description" (Text)

4. VALID IMAGE REQUIREMENTS:
   - File types: JPEG, PNG, WebP, GIF
   - Max size: 5MB
   - Field name: "thumbnail"

5. EXAMPLE RESPONSE:
   {
     "id": 1,
     "title": "My Blog Title",
     "thumbnail": "https://supabase-url/storage/...",
     "status": "published",
     ...
   }

6. UPDATE BLOG WITH NEW THUMBNAIL:
   - Method: PATCH/PUT
   - URL: http://127.0.0.1:8000/api/blogs/teacher/blogs/{id}/
   - Same form-data structure as creation

💡 ADVANTAGES OF SINGLE ENDPOINT:
- ✅ Upload thumbnail and create blog in one request
- ✅ No need for separate upload steps
- ✅ Simpler workflow for frontend/mobile apps
- ✅ Atomic operation (both succeed or both fail)
- ✅ Better user experience

🔄 WORKFLOW:
1. Prepare blog data + thumbnail file
2. Send single POST request with form-data
3. Receive complete blog response with thumbnail URL
4. Blog is ready for public viewing
""")

if __name__ == "__main__":
    # Install PIL if not available
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow for image generation...")
        os.system("pip install Pillow")
        from PIL import Image
    
    try:
        test_blog_creation_with_thumbnail()
        print_postman_guide()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")
