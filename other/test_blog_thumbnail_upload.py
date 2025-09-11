#!/usr/bin/env python3
"""
Blog Thumbnail Upload API Test Script
Tests the new thumbnail upload endpoint for teachers to upload blog images
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
    img = Image.new('RGB', size, color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes

def test_thumbnail_upload():
    """Test the blog thumbnail upload functionality"""
    print("="*60)
    print("BLOG THUMBNAIL UPLOAD API TEST")
    print("="*60)
    
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
    
    # Step 2: Test thumbnail upload - Valid image
    print("\n2. Testing thumbnail upload (Valid JPEG)...")
    
    # Create test image
    test_image = create_test_image("test_thumb.jpg", (800, 600), "JPEG")
    
    files = {
        'thumbnail': ('test_thumbnail.jpg', test_image, 'image/jpeg')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        headers=headers,
        files=files
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Thumbnail upload successful!")
        thumbnail_url = response.json().get('thumbnail_url')
        print(f"📷 Thumbnail URL: {thumbnail_url}")
        
        # Save the URL for blog creation test
        uploaded_thumbnail_url = thumbnail_url
    else:
        print("❌ Thumbnail upload failed!")
        return
    
    # Step 3: Test different image formats
    print("\n3. Testing PNG upload...")
    
    test_image_png = create_test_image("test_thumb.png", (800, 600), "PNG")
    files_png = {
        'thumbnail': ('test_thumbnail.png', test_image_png, 'image/png')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        headers=headers,
        files=files_png
    )
    
    print(f"PNG Upload Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ PNG upload successful!")
    else:
        print(f"❌ PNG upload failed: {response.json()}")
    
    # Step 4: Test file size validation (create large image)
    print("\n4. Testing file size validation...")
    
    # Create a large image (simulating >5MB)
    large_image = create_test_image("large_thumb.jpg", (4000, 3000), "JPEG")
    files_large = {
        'thumbnail': ('large_thumbnail.jpg', large_image, 'image/jpeg')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        headers=headers,
        files=files_large
    )
    
    print(f"Large Image Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ File size validation working!")
        print(f"Error message: {response.json().get('error')}")
    else:
        print("⚠️ File size validation might not be working properly")
    
    # Step 5: Test invalid file type
    print("\n5. Testing invalid file type...")
    
    # Create a text file pretending to be an image
    fake_image = BytesIO(b"This is not an image file")
    files_invalid = {
        'thumbnail': ('fake_image.txt', fake_image, 'text/plain')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        headers=headers,
        files=files_invalid
    )
    
    print(f"Invalid File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ File type validation working!")
        print(f"Error message: {response.json().get('error')}")
    else:
        print("⚠️ File type validation might not be working properly")
    
    # Step 6: Test missing file
    print("\n6. Testing missing file...")
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        headers=headers,
        files={}
    )
    
    print(f"Missing File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Missing file validation working!")
        print(f"Error message: {response.json().get('error')}")
    else:
        print("⚠️ Missing file validation might not be working properly")
    
    # Step 7: Test blog creation with uploaded thumbnail
    print("\n7. Testing blog creation with uploaded thumbnail...")
    
    blog_data = {
        "title": "Test Blog with Uploaded Thumbnail",
        "content": "This blog was created with an uploaded thumbnail image.",
        "thumbnail": uploaded_thumbnail_url,
        "status": "published",
        "tags": ["test", "upload", "thumbnail"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        json=blog_data
    )
    
    print(f"Blog Creation Status: {response.status_code}")
    if response.status_code == 201:
        print("✅ Blog created successfully with uploaded thumbnail!")
        blog_data = response.json()
        print(f"📝 Blog ID: {blog_data.get('id')}")
        print(f"📷 Blog Thumbnail: {blog_data.get('thumbnail')}")
    else:
        print(f"❌ Blog creation failed: {response.json()}")
    
    # Step 8: Test without authentication
    print("\n8. Testing upload without authentication...")
    
    test_image_unauth = create_test_image("unauth_thumb.jpg", (400, 300), "JPEG")
    files_unauth = {
        'thumbnail': ('unauth_thumbnail.jpg', test_image_unauth, 'image/jpeg')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/upload-thumbnail/",
        files=files_unauth  # No headers
    )
    
    print(f"Unauthenticated Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Authentication required validation working!")
    else:
        print("⚠️ Authentication validation might not be working properly")
    
    print("\n" + "="*60)
    print("THUMBNAIL UPLOAD TESTS COMPLETED")
    print("="*60)

def test_postman_guide():
    """Print guide for testing with Postman"""
    print("\n" + "="*60)
    print("POSTMAN TESTING GUIDE - BLOG THUMBNAIL UPLOAD")
    print("="*60)
    
    print("""
📋 POSTMAN SETUP FOR THUMBNAIL UPLOAD:

1. CREATE NEW REQUEST:
   - Method: POST
   - URL: http://127.0.0.1:8000/api/blogs/teacher/blogs/upload-thumbnail/

2. HEADERS:
   - Authorization: Token YOUR_TOKEN_HERE
   - Content-Type: multipart/form-data (automatically set)

3. BODY:
   - Select "form-data"
   - Key: "thumbnail" (set type to "File")
   - Value: Select your image file (JPEG, PNG, WebP, GIF)

4. VALID IMAGE REQUIREMENTS:
   - File types: JPEG, PNG, WebP, GIF
   - Max size: 5MB
   - Recommended: 800x600 or similar aspect ratio

5. EXPECTED RESPONSE (Success):
   {
     "message": "Thumbnail uploaded successfully",
     "thumbnail_url": "https://your-supabase-url/storage/v1/object/public/blog-images/...",
     "filename": "blog_thumbnails/user_id/uuid.jpg"
   }

6. USE RETURNED URL:
   - Copy the "thumbnail_url" from response
   - Use it in blog creation requests as the "thumbnail" field

7. CREATE BLOG WITH UPLOADED THUMBNAIL:
   POST http://127.0.0.1:8000/api/blogs/teacher/blogs/
   {
     "title": "My Blog",
     "content": "Blog content...",
     "thumbnail": "PASTE_UPLOADED_URL_HERE",
     "status": "published"
   }

💡 TIPS:
- Always upload thumbnail first, then create blog
- Save the returned URL for blog creation
- Test with different image formats and sizes
- Ensure your Supabase storage bucket "blog-images" exists
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
        test_thumbnail_upload()
        test_postman_guide()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")
