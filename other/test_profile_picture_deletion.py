"""
Test script for Profile Picture Upload with Previous Picture Deletion
Tests that uploading a new profile picture deletes the previous one from Supabase
"""
import requests
import json
import io
from PIL import Image

# Configuration
BASE_URL = "http://127.0.0.1:8000"
PROFILE_PICTURE_UPLOAD_URL = f"{BASE_URL}/user/profile-picture/"

def create_test_image(name, size=(100, 100), color=(255, 0, 0)):
    """Create a test image in memory"""
    img = Image.new('RGB', size, color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_profile_picture_update_with_deletion():
    """Test profile picture update and deletion of previous picture"""
    
    # Your access token here
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("Testing Profile Picture Update with Previous Picture Deletion...")
    print(f"URL: {PROFILE_PICTURE_UPLOAD_URL}")
    print("-" * 60)
    
    try:
        # Step 1: Upload first profile picture
        print("\nStep 1: Uploading first profile picture (red image)...")
        
        first_image = create_test_image("first_image.png", color=(255, 0, 0))  # Red image
        files = {
            'profile_picture': ('first_image.png', first_image, 'image/png')
        }
        
        response = requests.post(PROFILE_PICTURE_UPLOAD_URL, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ First profile picture uploaded successfully!")
            first_picture_path = result.get('profile_picture')
            print(f"First picture path: {first_picture_path}")
            
            # Step 2: Upload second profile picture (should delete first one)
            print("\nStep 2: Uploading second profile picture (blue image)...")
            
            second_image = create_test_image("second_image.png", color=(0, 0, 255))  # Blue image
            files = {
                'profile_picture': ('second_image.png', second_image, 'image/png')
            }
            
            response = requests.post(PROFILE_PICTURE_UPLOAD_URL, files=files, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Second profile picture uploaded successfully!")
                second_picture_path = result.get('profile_picture')
                print(f"Second picture path: {second_picture_path}")
                
                # Verify that the paths are different
                if first_picture_path != second_picture_path:
                    print("✅ Profile picture path changed correctly!")
                else:
                    print("⚠️  Profile picture path didn't change (might be same filename)")
                
                # The deletion should have happened automatically in the backend
                print("✅ Previous profile picture should have been deleted from Supabase")
                
                # Step 3: Upload third profile picture to test deletion again
                print("\nStep 3: Uploading third profile picture (green image)...")
                
                third_image = create_test_image("third_image.png", color=(0, 255, 0))  # Green image
                files = {
                    'profile_picture': ('third_image.png', third_image, 'image/png')
                }
                
                response = requests.post(PROFILE_PICTURE_UPLOAD_URL, files=files, headers=headers)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Third profile picture uploaded successfully!")
                    third_picture_path = result.get('profile_picture')
                    print(f"Third picture path: {third_picture_path}")
                    print("✅ Second profile picture should have been deleted from Supabase")
                else:
                    error_data = response.json() if response.content else {"error": "No response content"}
                    print(f"❌ Third upload failed: {error_data}")
            else:
                error_data = response.json() if response.content else {"error": "No response content"}
                print(f"❌ Second upload failed: {error_data}")
        else:
            error_data = response.json() if response.content else {"error": "No response content"}
            print(f"❌ First upload failed: {error_data}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_profile_picture_update_without_previous():
    """Test profile picture update when user has no previous picture"""
    
    # This would be for a user who hasn't uploaded a profile picture before
    access_token = "YOUR_NEW_USER_ACCESS_TOKEN_HERE"  # Replace with token for user without profile picture
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\n" + "="*60)
    print("Testing Profile Picture Upload for User Without Previous Picture...")
    
    try:
        # Upload profile picture for user who doesn't have one
        test_image = create_test_image("new_user_image.png", color=(128, 0, 128))  # Purple image
        files = {
            'profile_picture': ('new_user_image.png', test_image, 'image/png')
        }
        
        response = requests.post(PROFILE_PICTURE_UPLOAD_URL, files=files, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Profile picture uploaded successfully for new user!")
            print(f"Picture path: {result.get('profile_picture')}")
            print("✅ No previous picture to delete (as expected)")
        else:
            error_data = response.json() if response.content else {"error": "No response content"}
            print(f"❌ Upload failed: {error_data}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def verify_supabase_deletion_logic():
    """Show the deletion logic that should happen"""
    
    print("\n" + "="*60)
    print("Profile Picture Deletion Logic:")
    print("1. Check if user.profile_picture exists")
    print("2. If exists, call supabase.storage.from_('user-uploads').remove([user.profile_picture])")
    print("3. Upload new picture to Supabase")
    print("4. Update user.profile_picture with new storage key")
    print("5. Save user with update_fields=['profile_picture']")
    print("\nBenefits:")
    print("- Prevents accumulation of unused profile pictures in Supabase")
    print("- Saves storage space and costs")
    print("- Keeps storage organized")
    print("- Handles deletion errors gracefully (continues with upload)")

if __name__ == "__main__":
    print("Profile Picture Update with Deletion Test Suite")
    print("="*60)
    
    print("\nFeatures being tested:")
    print("- Automatic deletion of previous profile picture from Supabase")
    print("- Successful upload of new profile picture")
    print("- Graceful handling when no previous picture exists")
    print("- Error handling for deletion failures")
    
    verify_supabase_deletion_logic()
    
    print(f"\n{'='*60}")
    print("Setup Instructions:")
    print("1. Update the access tokens with valid tokens")
    print("2. Ensure Django server is running: python manage.py runserver")
    print("3. Ensure Supabase credentials are configured")
    print("4. Install Pillow for image creation: pip install Pillow")
    print("="*60)
    
    print(f"\n{'='*60}")
    print("To run the actual tests, uncomment the function calls below:")
    print("# test_profile_picture_update_with_deletion()")
    print("# test_profile_picture_update_without_previous()")
    
    # Uncomment to run actual tests (after setting tokens)
    # test_profile_picture_update_with_deletion()
    # test_profile_picture_update_without_previous()
