"""
Test script to verify database connection and user name fetching
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8001"
TEST_DB_URL = f"{BASE_URL}/test-db"
START_CHAT_URL = f"{BASE_URL}/chats/start/"

def test_database_connection():
    """Test if the database connection is working"""
    
    print("Testing Database Connection")
    print(f"URL: {TEST_DB_URL}")
    print("="*50)
    
    try:
        response = requests.get(TEST_DB_URL)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Message: {data['message']}")
            
            if data['status'] == 'success':
                print("✅ Database connection working!")
                print(f"Total users in database: {data['user_count']}")
                
                if data['sample_user']:
                    sample = data['sample_user']
                    print(f"Sample user: {sample['first_name']} {sample['last_name']} ({sample['email']})")
                    print(f"Sample user role: {sample['role']}")
                else:
                    print("No users found in database")
                    
            else:
                print("❌ Database connection failed!")
                print(f"Error: {data['message']}")
                
                if 'solution' in data:
                    print(f"Solution: {data['solution']}")
                    
                if 'config' in data:
                    print("Database config:")
                    for key, value in data['config'].items():
                        print(f"  {key}: {value}")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server.")
        print("Make sure the server is running:")
        print("uvicorn fastapi_chat_fixed:app --reload --port 8001")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_chat_with_correct_names():
    """Test chat creation with corrected name fetching"""
    
    print("\n" + "="*50)
    print("Testing Chat Creation with Correct Names")
    print(f"URL: {START_CHAT_URL}")
    
    # Test data - replace with actual UUIDs from your system
    test_data = {
        "student_id": "a6e13d11-9bd4-4561-9e0b-0d199670d49e",
        "teacher_id": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
    }
    
    try:
        print(f"\nRequest Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(START_CHAT_URL, json=test_data)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            chat_data = response.json()
            print("✅ Chat creation successful!")
            
            print(f"\n=== Student Information ===")
            student = chat_data.get('student_details', {})
            print(f"ID: {student.get('id', 'N/A')}")
            print(f"Email: {student.get('email', 'N/A')}")
            print(f"First Name: '{student.get('first_name', '')}'")
            print(f"Last Name: '{student.get('last_name', '')}'")
            print(f"Full Name: {student.get('first_name', '')} {student.get('last_name', '')}")
            print(f"Role: {student.get('role', 'N/A')}")
            
            if 'error' in student:
                print(f"⚠️  Error: {student['error']}")
            
            print(f"\n=== Teacher Information ===")
            teacher = chat_data.get('teacher_details', {})
            print(f"ID: {teacher.get('id', 'N/A')}")
            print(f"Email: {teacher.get('email', 'N/A')}")
            print(f"First Name: '{teacher.get('first_name', '')}'")
            print(f"Last Name: '{teacher.get('last_name', '')}'")
            print(f"Full Name: {teacher.get('first_name', '')} {teacher.get('last_name', '')}")
            print(f"Role: {teacher.get('role', 'N/A')}")
            
            if 'error' in teacher:
                print(f"⚠️  Error: {teacher['error']}")
            
            # Check if names are now correctly populated
            student_name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
            teacher_name = f"{teacher.get('first_name', '')} {teacher.get('last_name', '')}".strip()
            
            print(f"\n=== Name Verification ===")
            if student_name and student_name != " ":
                print(f"✅ Student name correctly fetched: '{student_name}'")
            else:
                print(f"❌ Student name empty or missing")
                
            if teacher_name and teacher_name != " ":
                print(f"✅ Teacher name correctly fetched: '{teacher_name}'")
            else:
                print(f"❌ Teacher name empty or missing")
            
            print(f"\n=== Full Response ===")
            print(json.dumps(chat_data, indent=2))
            
        else:
            print(f"❌ Chat creation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def installation_guide():
    """Show installation guide for required dependencies"""
    
    print("\n" + "="*60)
    print("=== Installation Guide ===")
    
    print("\n1. Install required Python package:")
    print("   pip install psycopg2-binary")
    print("   # or alternatively: pip install psycopg2")
    
    print("\n2. Update your FastAPI file:")
    print("   Replace fastapi_chat.py with fastapi_chat_fixed.py")
    print("   Or copy the database connection code")
    
    print("\n3. Start the FastAPI server:")
    print("   uvicorn fastapi_chat_fixed:app --reload --port 8001")
    
    print("\n4. Verify database settings:")
    print("   Make sure your Django database is accessible")
    print("   Check connection parameters in fastapi_chat_fixed.py")
    
    print("\n5. Test the connection:")
    print(f"   Visit: {TEST_DB_URL}")
    print(f"   Or run this test script")

if __name__ == "__main__":
    print("=== FastAPI Chat Name Fix Testing ===")
    
    # Show installation guide
    installation_guide()
    
    print("\n" + "="*60)
    print("Running Tests...")
    
    # Test database connection first
    test_database_connection()
    
    # Test chat creation with correct names
    test_chat_with_correct_names()
    
    print("\n" + "="*60)
    print("Testing completed!")
    print("\nIf names are still incorrect:")
    print("1. Check if psycopg2-binary is installed")
    print("2. Verify database connection parameters")
    print("3. Ensure user data exists in core_user table")
    print("4. Check the /test-db endpoint for debugging")
    print("="*60)
