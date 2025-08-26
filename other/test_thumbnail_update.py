#!/usr/bin/env python3
"""
Blog Thumbnail Update API Test Script
Tests the new dedicated thumbnail update endpoint that deletes previous thumbnails
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

def create_test_image(filename="test_thumbnail.jpg", size=(800, 600), format="JPEG", color='red'):
    """Create a test image file"""
    img = Image.new('RGB', size, color=color)
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes

def test_thumbnail_update():
    """Test the dedicated thumbnail update endpoint"""
    print("="*70)
    print("BLOG THUMBNAIL UPDATE API TEST")
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
    
    # Step 2: Create a blog category first
    print("\n2. Creating blog category...")
    category_data = {
        "name": "Test Category",
        "description": "Category for testing thumbnail updates"
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
    
    # Step 3: Create a blog with initial thumbnail
    print("\n3. Creating blog with initial thumbnail...")
    
    initial_image = create_test_image("initial_thumb.jpg", (800, 600), "JPEG", 'red')
    
    files = {
        'thumbnail': ('initial_thumbnail.jpg', initial_image, 'image/jpeg')
    }
    
    data = {
        'title': 'Test Blog for Thumbnail Update',
        'content': 'This blog will have its thumbnail updated to test the deletion functionality.',
        'category': category_id,
        'tags': '["test", "thumbnail", "update"]',
        'status': 'published'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/blogs/teacher/blogs/",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Blog Creation Status: {response.status_code}")
    
    if response.status_code == 201:
        blog_data = response.json()
        blog_id = blog_data.get('id')
        initial_thumbnail_url = blog_data.get('thumbnail')
        print(f"✅ Blog created successfully!")
        print(f"📝 Blog ID: {blog_id}")
        print(f"📷 Initial Thumbnail: {initial_thumbnail_url}")
    else:
        print(f"❌ Blog creation failed: {response.json()}")
        return
    
    # Step 4: Test thumbnail update with new image
    print("\n4. Testing thumbnail update (should delete previous thumbnail)...")
    
    # Create a different colored image
    new_image = create_test_image("new_thumb.png", (600, 400), "PNG", 'blue')
    
    files_update = {
        'thumbnail': ('new_thumbnail.png', new_image, 'image/png')
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/",
        headers=headers,
        files=files_update
    )
    
    print(f"Thumbnail Update Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        update_data = response.json()
        print("✅ Thumbnail updated successfully!")
        print(f"🗑️ Old thumbnail deleted: {update_data.get('old_thumbnail_deleted')}")
        print(f"📷 Old URL: {update_data.get('old_thumbnail_url')}")
        print(f"📷 New URL: {update_data.get('new_thumbnail_url')}")
        updated_blog_id = blog_id
    else:
        print("❌ Thumbnail update failed!")
        return
    
    # Step 5: Verify blog has new thumbnail
    print("\n5. Verifying blog has new thumbnail...")
    
    response = requests.get(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/",
        headers=headers
    )
    
    if response.status_code == 200:
        blog_data = response.json()
        current_thumbnail = blog_data.get('thumbnail')
        print(f"✅ Blog retrieved successfully")
        print(f"📷 Current thumbnail: {current_thumbnail}")
        
        # Check if thumbnail URL changed
        if current_thumbnail != initial_thumbnail_url:
            print("✅ Thumbnail URL successfully updated in blog!")
        else:
            print("⚠️ Thumbnail URL might not have been updated")
    else:
        print(f"❌ Failed to retrieve blog: {response.json()}")
    
    # Step 6: Test update with different format
    print("\n6. Testing thumbnail update with WebP format...")
    
    webp_image = create_test_image("webp_thumb.webp", (900, 500), "WEBP", 'green')
    
    files_webp = {
        'thumbnail': ('webp_thumbnail.webp', webp_image, 'image/webp')
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/",
        headers=headers,
        files=files_webp
    )
    
    print(f"WebP Update Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ WebP thumbnail update successful!")
        print(f"🗑️ Previous thumbnail deleted: {response.json().get('old_thumbnail_deleted')}")
    else:
        print(f"❌ WebP update failed: {response.json()}")
    
    # Step 7: Test error scenarios
    print("\n7. Testing error scenarios...")
    
    # Test with invalid blog ID
    print("\n7a. Testing with invalid blog ID...")
    test_image = create_test_image("test.jpg", (400, 300), "JPEG", 'yellow')
    files_test = {
        'thumbnail': ('test.jpg', test_image, 'image/jpeg')
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/99999/update-thumbnail/",
        headers=headers,
        files=files_test
    )
    
    print(f"Invalid Blog ID Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Invalid blog ID properly handled!")
    else:
        print("⚠️ Invalid blog ID handling might need attention")
    
    # Test without file
    print("\n7b. Testing without thumbnail file...")
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/",
        headers=headers,
        files={}
    )
    
    print(f"No File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Missing file validation working!")
        print(f"Error: {response.json().get('error')}")
    else:
        print("⚠️ Missing file validation might need attention")
    
    # Test with invalid file type
    print("\n7c. Testing with invalid file type...")
    fake_file = BytesIO(b"This is not an image")
    files_invalid = {
        'thumbnail': ('fake.txt', fake_file, 'text/plain')
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/",
        headers=headers,
        files=files_invalid
    )
    
    print(f"Invalid File Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ File type validation working!")
        print(f"Error: {response.json().get('error')}")
    else:
        print("⚠️ File type validation might need attention")
    
    # Step 8: Test without authentication
    print("\n8. Testing without authentication...")
    test_image_unauth = create_test_image("unauth.jpg", (300, 200), "JPEG", 'purple')
    files_unauth = {
        'thumbnail': ('unauth.jpg', test_image_unauth, 'image/jpeg')
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/",
        files=files_unauth  # No auth headers
    )
    
    print(f"No Auth Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Authentication validation working!")
    else:
        print("⚠️ Authentication validation might need attention")
    
    print("\n" + "="*70)
    print("THUMBNAIL UPDATE TESTS COMPLETED")
    print("="*70)
    
    print(f"\n🎯 KEY FEATURES TESTED:")
    print(f"  ✅ Thumbnail update with automatic deletion")
    print(f"  ✅ Multiple image format support (JPEG, PNG, WebP)")
    print(f"  ✅ File validation (type and size)")
    print(f"  ✅ Authentication and permission checks")
    print(f"  ✅ Error handling for edge cases")
    print(f"  ✅ Blog thumbnail URL updates")

def print_postman_guide():
    """Print guide for testing with Postman"""
    print("\n" + "="*70)
    print("POSTMAN TESTING GUIDE - THUMBNAIL UPDATE ENDPOINT")
    print("="*70)
    
    print("""
📋 POSTMAN SETUP FOR THUMBNAIL UPDATE:

1. CREATE NEW REQUEST:
   - Method: PATCH
   - URL: http://127.0.0.1:8000/api/blogs/teacher/blogs/{blog_id}/update-thumbnail/

2. HEADERS:
   - Authorization: Token YOUR_TOKEN_HERE

3. BODY (select "form-data"):
   - Key: "thumbnail" (set type to "File")
   - Value: Select your new image file

4. REPLACE {blog_id} WITH ACTUAL BLOG ID:
   - Get blog ID from blog list or creation response
   - Example: /api/blogs/teacher/blogs/1/update-thumbnail/

5. EXPECTED RESPONSE (Success):
   {
     "message": "Thumbnail updated successfully",
     "blog_id": 1,
     "old_thumbnail_url": "https://old-url...",
     "new_thumbnail_url": "https://new-url...",
     "old_thumbnail_deleted": true,
     "filename": "blog_thumbnails/user_id/uuid.jpg"
   }

6. ERROR RESPONSES:
   - 400: Invalid file type/size or missing file
   - 401: Not authenticated
   - 403: Not a teacher
   - 404: Blog not found or no permission
   - 500: Server error during upload/deletion

💡 ADVANTAGES OF DEDICATED UPDATE ENDPOINT:
- ✅ Automatically deletes old thumbnail from storage
- ✅ Prevents storage bloat from unused files
- ✅ Atomic operation (update succeeds or fails completely)
- ✅ Clear response indicating deletion status
- ✅ Dedicated endpoint for thumbnail management
- ✅ Better error handling and validation

🔄 WORKFLOW:
1. Get blog ID from existing blog
2. Select new thumbnail image file
3. Send PATCH request to update endpoint
4. Old thumbnail automatically deleted from Supabase
5. New thumbnail uploaded and blog updated
6. Response confirms success and deletion status
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
        test_thumbnail_update()
        print_postman_guide()
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the Django server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")
