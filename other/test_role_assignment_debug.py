"""
Enhanced test script for debugging role assignment in Django chats endpoint
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
CHATS_URL = f"{BASE_URL}/accounts/supabase/chats/"

def test_enhanced_role_assignment():
    """Test the enhanced role assignment with detailed analysis"""
    
    # You'll need to provide a valid access token for testing
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # Replace with actual token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("Testing Enhanced Role Assignment in Django Chats Endpoint")
    print(f"URL: {CHATS_URL}")
    print("="*70)
    
    try:
        response = requests.get(CHATS_URL, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            chats = response.json()
            print("✅ Chats endpoint successful!")
            print(f"Found {len(chats)} chats")
            
            if chats:
                for i, chat in enumerate(chats, 1):
                    print(f"\n{'='*50}")
                    print(f"CHAT {i} ANALYSIS")
                    print(f"{'='*50}")
                    
                    print(f"Chat ID: {chat['id']}")
                    print(f"Created: {chat['created_at']}")
                    print(f"Roles Identified: {chat['roles_identified']}")
                    
                    if 'role_assignment_method' in chat:
                        print(f"Assignment Method: {chat['role_assignment_method']}")
                    
                    print(f"\nCURRENT ASSIGNMENT:")
                    print(f"Student ID: {chat['student_id']}")
                    print(f"Student Name: {chat['student_name']}")
                    print(f"Teacher ID: {chat['teacher_id']}")
                    print(f"Teacher Name: {chat['teacher_name']}")
                    
                    # Analyze the participants
                    if 'participants' in chat:
                        print(f"\nPARTICIPANT DETAILS:")
                        for j, participant in enumerate(chat['participants'], 1):
                            current_indicator = " (YOU)" if participant['is_current_user'] else ""
                            print(f"  Participant {j}: {participant['name']}{current_indicator}")
                            print(f"    ID: {participant['id']}")
                            print(f"    Role in metadata: {participant['role']}")
                            print(f"    Is current user: {participant['is_current_user']}")
                    
                    # Cross-reference with user_info
                    if 'user_info' in chat:
                        print(f"\nUSER INFO VERIFICATION:")
                        for user_id, info in chat['user_info'].items():
                            assigned_role = "STUDENT" if user_id == chat['student_id'] else "TEACHER"
                            print(f"  {user_id}:")
                            print(f"    Name: {info['name']}")
                            print(f"    Metadata Role: {info['role']}")
                            print(f"    Assigned As: {assigned_role}")
                    
                    # Suggest corrections
                    print(f"\nSUGGESTED ANALYSIS:")
                    if not chat['roles_identified']:
                        print("⚠️  Roles could not be determined from metadata")
                        print("💡 Possible reasons:")
                        print("   - Users don't have 'role' field in their metadata")
                        print("   - Role values are not 'STUDENT' or 'TEACHER'")
                        print("   - Metadata is missing or incomplete")
                        
                        if 'participants' in chat:
                            current_user = next((p for p in chat['participants'] if p['is_current_user']), None)
                            other_user = next((p for p in chat['participants'] if not p['is_current_user']), None)
                            
                            if current_user and other_user:
                                print(f"\n💡 Based on current user context:")
                                print(f"   Current user: {current_user['name']} ({current_user['id']})")
                                print(f"   Other user: {other_user['name']} ({other_user['id']})")
                                print(f"   Current assignment assumes current user is student")
                    else:
                        print("✅ Roles were successfully identified from metadata")
                    
                    print(f"\n{'-'*50}")
            else:
                print("ℹ️  No chats found for this user")
                
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your access token.")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django server is running on port 8000.")
    except Exception as e:
        print(f"❌ Error: {e}")

def suggest_metadata_fix():
    """Suggest how to fix the metadata issue"""
    
    print("\n" + "="*70)
    print("METADATA FIX SUGGESTIONS")
    print("="*70)
    
    print("\nThe issue appears to be that users have 'role': 'UNKNOWN' in their metadata.")
    print("This means the Supabase user metadata doesn't contain proper role information.")
    
    print("\n1. CHECK SUPABASE USER METADATA:")
    print("   Users should have metadata like:")
    print(json.dumps({
        "role": "STUDENT",  # or "TEACHER"
        "first_name": "John",
        "last_name": "Doe"
    }, indent=4))
    
    print("\n2. UPDATE USER METADATA:")
    print("   You can update user metadata in Supabase:")
    print("   - Via Supabase Dashboard > Authentication > Users")
    print("   - Via API when users register or update their profile")
    print("   - Via Django admin if you have a sync mechanism")
    
    print("\n3. EXPECTED ROLE VALUES:")
    print("   - 'STUDENT' (exactly this case)")
    print("   - 'TEACHER' (exactly this case)")
    print("   - Any other value will be treated as 'UNKNOWN'")
    
    print("\n4. ALTERNATIVE SOLUTIONS:")
    print("   a) Update the Django code to use different role field names")
    print("   b) Add role detection based on user presence in teacher/student tables")
    print("   c) Use a different strategy for role assignment")

def test_with_known_roles():
    """Test what happens with proper role metadata"""
    
    print("\n" + "="*70)
    print("TESTING WITH PROPER ROLES")
    print("="*70)
    
    print("\nIf the users had proper metadata:")
    
    example_correct = {
        "id": "ddef980d-3d99-460c-97c1-ef68b6a1ef24",
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e",
        "student_name": "Jane Student",
        "teacher_name": "John Teacher",
        "roles_identified": True,
        "user_info": {
            "a6e13d11-9bd4-4561-9e0b-0d199670d49e": {
                "name": "Jane Student",
                "role": "STUDENT"
            },
            "30139770-0d26-4e9e-8b36-8efb33ed7b2e": {
                "name": "John Teacher",
                "role": "TEACHER"
            }
        }
    }
    
    print("Expected response with correct roles:")
    print(json.dumps(example_correct, indent=2))

if __name__ == "__main__":
    print("=== Enhanced Role Assignment Testing ===")
    
    # Show metadata fix suggestions
    suggest_metadata_fix()
    
    # Show what correct data looks like
    test_with_known_roles()
    
    print("\n" + "="*70)
    print("SETUP INSTRUCTIONS:")
    print("1. Update the access_token variable with a valid user token")
    print("2. Make sure Django server is running: python manage.py runserver")
    print("3. Run the test to see detailed role assignment analysis")
    print("4. Check Supabase user metadata and update roles if needed")
    print("="*70)
    
    # Run the main test
    test_enhanced_role_assignment()
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("1. If roles are still 'UNKNOWN', update Supabase user metadata")
    print("2. Ensure users have 'role': 'STUDENT' or 'role': 'TEACHER'")
    print("3. Re-test the endpoint after updating metadata")
    print("4. Consider implementing role detection from Django models if needed")
    print("="*70)
