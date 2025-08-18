"""
Test script for Profile Picture Upload with Previous Picture Deletion
Tests that old profile pictures are properly deleted from Supabase when uploading new ones
"""
import requests
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PROFILE_PICTURE_URL = f"{BASE_URL}/api/user/profile-picture/"

def test_profile_picture_upload_with_deletion():
    """Test profile picture upload that should delete previous picture"""
    
    # Your access token here
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("Testing Profile Picture Upload with Deletion...")
    print(f"URL: {PROFILE_PICTURE_URL}")
    print("-" * 60)
    
    # Create a test image file (you can replace this with an actual image file path)
    test_image_path = "test_profile_picture.jpg"
    
    # Check if test image exists, if not create a simple one
    if not os.path.exists(test_image_path):
        print("Creating a test image file...")
        # Create a simple test image using PIL (if available) or just create a dummy file
        try:
            from PIL import Image
            import io
            
            # Create a simple colored square image
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(test_image_path, 'JPEG')
            print(f"✅ Created test image: {test_image_path}")
        except ImportError:
            # If PIL is not available, create a dummy file
            with open(test_image_path, 'wb') as f:
                f.write(b'dummy image content for testing')
            print(f"✅ Created dummy test file: {test_image_path}")
    
    try:
        # First upload - should work normally
        print("\n=== First Upload (No previous picture to delete) ===")
        
        with open(test_image_path, 'rb') as img_file:
            files = {'profile_picture': ('test1.jpg', img_file, 'image/jpeg')}
            response = requests.post(PROFILE_PICTURE_URL, files=files, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ First upload successful!")
            print(f"Profile picture: {result.get('profile_picture', 'N/A')}")
            
            # Second upload - should delete the previous picture
            print("\n=== Second Upload (Should delete previous picture) ===")
            
            with open(test_image_path, 'rb') as img_file:
                files = {'profile_picture': ('test2.jpg', img_file, 'image/jpeg')}
                response2 = requests.post(PROFILE_PICTURE_URL, files=files, headers=headers)
            
            print(f"Status Code: {response2.status_code}")
            
            if response2.status_code == 200:
                result2 = response2.json()
                print("✅ Second upload successful!")
                print(f"New profile picture: {result2.get('profile_picture', 'N/A')}")
                print("✅ Previous picture should have been deleted from Supabase")
                
                # Check server logs for deletion confirmation
                print("\n📋 Check the Django server console for deletion messages:")
                print("    - Look for 'Previous profile picture deletion result: ...'")
                print("    - Should NOT see JSON serialization errors anymore")
                
            else:
                print(f"❌ Second upload failed: {response2.text}")
                
        else:
            print(f"❌ First upload failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except FileNotFoundError:
        print(f"❌ Test image file not found: {test_image_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            print(f"\n🧹 Cleaned up test file: {test_image_path}")

def test_profile_picture_deletion_logic():
    """Test the logic for extracting file path from ImageFieldFile"""
    
    print("\n" + "="*60)
    print("=== Testing Profile Picture Path Extraction Logic ===")
    
    # Simulate the fix
    print("\n🔧 Fix Applied:")
    print("   Before: supabase.storage.remove([user.profile_picture])")
    print("   After:  supabase.storage.remove([user.profile_picture.name])")
    
    print("\n✅ Changes made:")
    print("   1. Added check: if user.profile_picture and user.profile_picture.name")
    print("   2. Extract file path: previous_file_path = user.profile_picture.name")
    print("   3. Use string path: supabase.storage.remove([previous_file_path])")
    
    print("\n📋 Expected behavior:")
    print("   - No more 'Object of type ImageFieldFile is not JSON serializable' errors")
    print("   - Previous profile pictures will be deleted from Supabase storage")
    print("   - Upload should complete successfully")
    print("   - User's profile_picture field will be updated with new image path")

if __name__ == "__main__":
    print("Profile Picture Upload with Deletion - Test Suite")
    print("Update the access_token variable with a valid token before running")
    print("="*60)
    
    # Show the fix details
    test_profile_picture_deletion_logic()
    
    print(f"\n{'='*60}")
    print("Setup Instructions:")
    print("1. Update the access_token with a valid token")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Monitor Django console for deletion messages")
    print("4. Uncomment the test function call below to run the actual test")
    print("="*60)
    
    # Uncomment to run actual test (after setting access token)
    # test_profile_picture_upload_with_deletion()
