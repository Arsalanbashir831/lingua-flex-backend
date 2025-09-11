"""
Database Connection Diagnosis Script
This script helps identify and fix database connection issues
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8001"
TEST_DB_URL = f"{BASE_URL}/test-db"

def diagnose_database_connection():
    """Diagnose database connection issues"""
    
    print("=== Database Connection Diagnosis ===")
    print(f"Testing URL: {TEST_DB_URL}")
    print()
    
    try:
        response = requests.get(TEST_DB_URL)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Analyze the response
            if data.get('status') == 'error':
                print("\n=== ERROR IDENTIFIED ===")
                print(f"Error: {data['message']}")
                
                if 'psycopg2 not installed' in data['message']:
                    print("\n🔧 SOLUTION: Install psycopg2")
                    print("Run this command:")
                    print("pip install psycopg2-binary")
                    
                elif 'Cannot connect to database' in data['message']:
                    print("\n🔧 SOLUTION: Fix database connection")
                    print("Check these settings:")
                    if 'config' in data:
                        for key, value in data['config'].items():
                            print(f"  {key}: {value}")
                    
                    print("\nTroubleshooting steps:")
                    print("1. Verify PostgreSQL is running")
                    print("2. Check database connection parameters")
                    print("3. Test connection manually")
                    
                if 'solution' in data:
                    print(f"\nRecommended action: {data['solution']}")
                    
            elif data.get('status') == 'success':
                print("\n✅ DATABASE CONNECTION WORKING!")
                print(f"User count: {data['user_count']}")
                if data['sample_user']:
                    sample = data['sample_user']
                    print(f"Sample user: {sample['first_name']} {sample['last_name']}")
                    
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI server")
        print("\nCheck if FastAPI server is running:")
        print("uvicorn fastapi_chat_fixed:app --reload --port 8001")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def provide_installation_guide():
    """Provide step-by-step installation guide"""
    
    print("\n" + "="*60)
    print("=== STEP-BY-STEP FIX GUIDE ===")
    
    print("\n1. INSTALL REQUIRED PACKAGE")
    print("   Run this command in your terminal:")
    print("   pip install psycopg2-binary")
    
    print("\n2. CHECK DJANGO DATABASE SETTINGS")
    print("   Open rag_app/settings.py and find DATABASES configuration")
    print("   Note down these values:")
    print("   - NAME (database name)")
    print("   - USER (database username)")
    print("   - PASSWORD (database password)")
    print("   - HOST (database host, usually localhost)")
    print("   - PORT (database port, usually 5432)")
    
    print("\n3. VERIFY POSTGRESQL IS RUNNING")
    print("   Check if PostgreSQL service is running:")
    print("   - Windows: Check Services or run 'pg_ctl status'")
    print("   - Linux/Mac: 'sudo systemctl status postgresql' or 'pg_ctl status'")
    
    print("\n4. TEST DATABASE CONNECTION MANUALLY")
    print("   Try connecting with psql:")
    print("   psql -h localhost -U your_username -d your_database")
    
    print("\n5. UPDATE FASTAPI CONFIGURATION (if needed)")
    print("   If Django settings don't work, manually set DB_CONFIG in fastapi_chat_fixed.py")
    
    print("\n6. RESTART FASTAPI SERVER")
    print("   uvicorn fastapi_chat_fixed:app --reload --port 8001")
    
    print("\n7. TEST AGAIN")
    print(f"   Visit: {TEST_DB_URL}")

def check_django_database_settings():
    """Help user check Django database settings"""
    
    print("\n" + "="*60)
    print("=== DJANGO DATABASE SETTINGS CHECK ===")
    
    print("\nPlease check your Django settings.py file:")
    print("Location: rag_app/settings.py")
    print("\nLook for DATABASES configuration like this:")
    
    print("""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',      # ← Note this
        'USER': 'your_username',           # ← Note this  
        'PASSWORD': 'your_password',       # ← Note this
        'HOST': 'localhost',               # ← Note this
        'PORT': '5432',                    # ← Note this
    }
}
""")
    
    print("Common database configurations:")
    print("1. Local PostgreSQL:")
    print("   HOST: localhost")
    print("   PORT: 5432")
    print("   NAME: postgres (or your project name)")
    print("   USER: postgres")
    print("   PASSWORD: your postgres password")
    
    print("\n2. Supabase PostgreSQL:")
    print("   HOST: db.your-project.supabase.co")
    print("   PORT: 5432")
    print("   NAME: postgres")
    print("   USER: postgres")
    print("   PASSWORD: your supabase db password")
    
    print("\n3. Docker PostgreSQL:")
    print("   HOST: localhost or container name")
    print("   PORT: 5432")
    print("   NAME: your db name")
    print("   USER: your db user")
    print("   PASSWORD: your db password")

if __name__ == "__main__":
    print("🔍 DATABASE CONNECTION TROUBLESHOOTER")
    print("This script will help identify and fix the database connection issue.")
    
    # Step 1: Test current connection
    diagnose_database_connection()
    
    # Step 2: Provide fix guide
    provide_installation_guide()
    
    # Step 3: Help with Django settings
    check_django_database_settings()
    
    print("\n" + "="*60)
    print("💡 QUICK FIXES TO TRY:")
    print("1. pip install psycopg2-binary")
    print("2. Check if PostgreSQL is running")
    print("3. Verify database credentials in settings.py")
    print("4. Test /test-db endpoint after each fix")
    print("="*60)
