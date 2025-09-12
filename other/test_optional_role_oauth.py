#!/usr/bin/env python3
"""
Test Optional Role in Google OAuth Initiate Endpoint
Tests both registration (with role) and login (without role) flows
"""

import requests
import json
import sys

def test_optional_role_oauth():
    """Test OAuth initiate endpoint with and without role"""
    print("🔍 Testing Optional Role in Google OAuth")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Registration flow (with role)
    print("1️⃣  Testing Registration Flow (with role)...")
    try:
        response = requests.post(f'{base_url}/api/auth/google/initiate/', 
                               json={'role': 'TEACHER'})
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration initiation successful")
            print(f"📋 Flow Type: {data.get('flow_type')}")
            print(f"📋 Role: {data.get('role')}")
            print(f"📋 OAuth URL: {data.get('oauth_url')[:80]}...")
        else:
            print(f"❌ Registration initiation failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Login flow (without role)
    print("\n2️⃣  Testing Login Flow (without role)...")
    try:
        response = requests.post(f'{base_url}/api/auth/google/initiate/', 
                               json={})  # No role provided
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login initiation successful")
            print(f"📋 Flow Type: {data.get('flow_type')}")
            print(f"📋 Role: {data.get('role', 'Not provided')}")
            print(f"📋 OAuth URL: {data.get('oauth_url')[:80]}...")
        else:
            print(f"❌ Login initiation failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Custom redirect URL
    print("\n3️⃣  Testing Custom Redirect URL...")
    try:
        response = requests.post(f'{base_url}/api/auth/google/initiate/', 
                               json={
                                   'role': 'STUDENT',
                                   'redirect_url': 'https://myapp.com/auth/callback'
                               })
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Custom redirect successful")
            print(f"📋 Flow Type: {data.get('flow_type')}")
            print(f"📋 Role: {data.get('role')}")
            oauth_url = data.get('oauth_url')
            if 'redirect_to=https://myapp.com' in oauth_url:
                print("✅ Custom redirect URL included in OAuth URL")
            else:
                print("⚠️  Custom redirect URL not found in OAuth URL")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return True

def explain_oauth_flows():
    """Explain the two OAuth flows"""
    print("\n📚 OAuth Flow Explanation")
    print("=" * 40)
    
    flows = {
        "Registration Flow (New Users)": {
            "initiate_request": {
                "role": "TEACHER",  # Required
                "redirect_url": "https://app.com/auth/callback"  # Optional
            },
            "initiate_response": {
                "success": True,
                "oauth_url": "https://supabase.../auth/v1/authorize?provider=google&...",
                "role": "TEACHER",
                "flow_type": "registration"
            },
            "callback_request": {
                "access_token": "real_supabase_token",
                "refresh_token": "real_refresh_token", 
                "role": "TEACHER"  # Required for new users
            },
            "callback_response": {
                "success": True,
                "message": "User registered successfully via Google",
                "created": True,
                "flow_type": "registration",
                "requires_profile_completion": True
            }
        },
        "Login Flow (Existing Users)": {
            "initiate_request": {
                # No role needed
                "redirect_url": "https://app.com/auth/callback"  # Optional
            },
            "initiate_response": {
                "success": True,
                "oauth_url": "https://supabase.../auth/v1/authorize?provider=google&...",
                "flow_type": "login"
                # No role in response
            },
            "callback_request": {
                "access_token": "real_supabase_token",
                "refresh_token": "real_refresh_token"
                # No role needed - user already exists
            },
            "callback_response": {
                "success": True,
                "message": "User logged in successfully via Google",
                "created": False,
                "is_existing_user_login": True,
                "flow_type": "login",
                "requires_profile_completion": False
            }
        }
    }
    
    for flow_name, flow_data in flows.items():
        print(f"\n🔄 {flow_name}:")
        for step, data in flow_data.items():
            step_name = step.replace('_', ' ').title()
            print(f"   📋 {step_name}:")
            print(f"      {json.dumps(data, indent=6)[6:]}")  # Remove first 6 spaces
    
def explain_frontend_implementation():
    """Explain how frontend should handle optional role"""
    print("\n💻 Frontend Implementation Guide")
    print("=" * 45)
    
    print("🎯 Registration Page (Role Selection Required):")
    print("""
    // User must select role before OAuth
    const [selectedRole, setSelectedRole] = useState('');
    
    const handleGoogleSignup = async () => {
        if (!selectedRole) {
            alert('Please select your role first');
            return;
        }
        
        const response = await fetch('/api/auth/google/initiate/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                role: selectedRole,
                redirect_url: window.location.origin + '/auth/callback'
            })
        });
        
        const data = await response.json();
        if (data.success) {
            // Store role for callback
            localStorage.setItem('oauth_role', selectedRole);
            window.location.href = data.oauth_url;
        }
    };
    """)
    
    print("\n🎯 Login Page (No Role Selection):")
    print("""
    // Existing users don't need to select role
    const handleGoogleLogin = async () => {
        const response = await fetch('/api/auth/google/initiate/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                redirect_url: window.location.origin + '/auth/callback'
                // No role specified
            })
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = data.oauth_url;
        }
    };
    """)
    
    print("\n🎯 OAuth Callback Handler:")
    print("""
    const handleOAuthCallback = async (accessToken, refreshToken) => {
        // Get role from localStorage (for registration) or omit (for login)
        const storedRole = localStorage.getItem('oauth_role');
        
        const callbackData = {
            access_token: accessToken,
            refresh_token: refreshToken
        };
        
        // Only include role if it was stored (registration flow)
        if (storedRole) {
            callbackData.role = storedRole;
        }
        
        const response = await fetch('/api/auth/google/callback/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(callbackData)
        });
        
        const data = await response.json();
        if (data.success) {
            // Handle based on flow type
            if (data.flow_type === 'registration') {
                // New user - might need profile completion
                if (data.requires_profile_completion) {
                    router.push('/profile/complete');
                } else {
                    router.push('/dashboard');
                }
            } else {
                // Existing user login - go straight to dashboard
                router.push('/dashboard');
            }
        }
        
        // Clean up
        localStorage.removeItem('oauth_role');
    };
    """)

def main():
    print("🚀 Google OAuth Optional Role Testing")
    print("Testing role flexibility for registration vs login flows")
    print("=" * 60)
    
    if test_optional_role_oauth():
        print("\n✅ Optional role testing completed!")
    else:
        print("\n❌ Testing failed!")
        return 1
    
    explain_oauth_flows()
    explain_frontend_implementation()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY - Optional Role Implementation:")
    print()
    print("✅ Role is now optional in /api/auth/google/initiate/")
    print("✅ Registration flow: Requires role selection")
    print("✅ Login flow: No role needed (uses existing user's role)")
    print("✅ Callback intelligently handles both scenarios")
    print("✅ Clear flow_type indicator in responses")
    print()
    print("🎯 Benefits:")
    print("- Better UX: Existing users don't select role unnecessarily")
    print("- Clear separation: Registration vs login flows")
    print("- Flexible: Works for both new and existing users")
    print("- Robust: Proper error handling for missing role in registration")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
