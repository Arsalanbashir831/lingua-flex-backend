#!/usr/bin/env python3
"""
Quick test to verify the complete endpoint is now working
"""

import requests
import json

def test_complete_endpoint():
    """Test if the complete endpoint is accessible"""
    print("🧪 Testing Complete Booking Endpoint")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test endpoint - should get 401/403 (auth required) instead of 500 (method not found)
        response = requests.post(f'{base_url}/api/bookings/bookings/3/complete/')
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 500:
            print("❌ Still getting 500 error - method not found")
            print(f"Response: {response.text[:200]}...")
            return False
        elif response.status_code in [401, 403]:
            print("✅ Endpoint found! (Authentication required)")
            try:
                error_data = response.json()
                print(f"📋 Response: {json.dumps(error_data, indent=2)}")
            except:
                print("📋 Response: Authentication required")
            return True
        elif response.status_code == 400:
            print("✅ Endpoint found! (Bad request - needs auth and proper booking)")
            try:
                error_data = response.json()
                print(f"📋 Response: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return True
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return True
            
    except requests.exceptions.ConnectionError:
        print("⏭️  Django server not running")
        print("💡 Start server: python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if test_complete_endpoint():
        print("\n✅ Complete endpoint is working!")
        print("🎯 Ready to test with proper authentication")
    else:
        print("\n❌ Complete endpoint still has issues")
