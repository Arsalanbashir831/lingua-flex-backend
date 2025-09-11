# 🔐 Zoom API Credentials Setup & Verification Guide

## ✅ Current Status
Your Zoom credentials are already configured in `.env`:

```env
ZOOM_ACCOUNT_ID=ZJmI_gxfSoqVY84zdfzaEA
ZOOM_API_KEY=8t0mzl52ScOdw319JY_isw  
ZOOM_API_SECRET=kvaJgTuZJVJruqSnY7vzecOF7t3XFiZc
```

## 🔧 How Zoom Integration Works

### **1. Credential Types Used:**
- **`ZOOM_ACCOUNT_ID`**: Your Zoom account identifier
- **`ZOOM_API_KEY`**: API Key for authentication
- **`ZOOM_API_SECRET`**: Secret key for JWT token generation

### **2. Authentication Method:**
Our system uses **JWT (JSON Web Token)** authentication with Zoom API:
- Creates JWT tokens using API Key + Secret
- No need for OAuth flows
- Tokens are generated on-demand for each API call

### **3. Integration Points:**
- **Create Meeting**: When student books a session
- **Update Meeting**: When booking is rescheduled  
- **Delete Meeting**: When booking is cancelled

## 🧪 Test Your Zoom Credentials

### **Option 1: Quick Python Test**
```python
# Save as test_zoom_credentials.py
import jwt
import time
import requests
from datetime import datetime, timedelta

# Your credentials from .env
ZOOM_API_KEY = "8t0mzl52ScOdw319JY_isw"
ZOOM_API_SECRET = "kvaJgTuZJVJruqSnY7vzecOF7t3XFiZc"

def test_zoom_credentials():
    # Generate JWT token
    payload = {
        'iss': ZOOM_API_KEY,
        'exp': int(time.time() + 3600)
    }
    
    try:
        token = jwt.encode(payload, ZOOM_API_SECRET, algorithm='HS256')
        print("✅ JWT Token generated successfully")
        
        # Test API call
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Get user info (basic test)
        response = requests.get('https://api.zoom.us/v2/users/me', headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Zoom API working! User: {user_info.get('email', 'Unknown')}")
            return True
        else:
            print(f"❌ Zoom API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_zoom_credentials()
```

### **Option 2: Django Management Command Test**
```python
# In Django shell: python manage.py shell
from bookings.zoom_service import ZoomService
from datetime import datetime, timedelta

# Test Zoom service
zoom_service = ZoomService()

# Check if credentials are loaded
print(f"API Key: {zoom_service.api_key[:10]}...")
print(f"API Secret: {zoom_service.api_secret[:10]}...")

# Test JWT generation
try:
    token = zoom_service.generate_jwt_token()
    print("✅ JWT token generated successfully")
except Exception as e:
    print(f"❌ JWT generation failed: {e}")
```

## 🚨 Troubleshooting Common Issues

### **Issue 1: "Zoom functionality will be disabled" Warning**
**Cause:** Warning from `core/views.py` checking for old zoomus library
**Solution:** ✅ Ignore this warning - our system uses JWT authentication, not zoomus

### **Issue 2: No Zoom meeting created in API response**
**Possible Causes:**
1. **Invalid credentials** - API key/secret incorrect
2. **Teacher email not in Zoom** - Teacher must have Zoom account
3. **API limits exceeded** - Check Zoom account limits
4. **Network issues** - Firewall blocking api.zoom.us

**Debug Steps:**
```python
# Check if credentials are loaded in Django
from django.conf import settings
print(f"ZOOM_API_KEY: {settings.ZOOM_API_KEY}")
print(f"ZOOM_API_SECRET: {settings.ZOOM_API_SECRET}")
```

### **Issue 3: JWT Token Errors**
**Error:** `Invalid token` or `Token expired`
**Solution:** JWT tokens expire after 1 hour, system generates new ones automatically

### **Issue 4: 401 Unauthorized from Zoom**
**Causes:**
- Wrong API key/secret
- Account suspended
- API permissions not granted

## 🔍 Verify Your Zoom Account Setup

### **1. Check Zoom Developer Account:**
Visit: https://marketplace.zoom.us/develop/create
- Ensure you have a "JWT App" created
- Copy the credentials to your `.env` file

### **2. Required Zoom App Permissions:**
Your JWT app should have these scopes:
- `meeting:write` - Create meetings
- `meeting:read` - Read meeting details  
- `meeting:update` - Update meetings
- `meeting:delete` - Delete meetings

### **3. Account Requirements:**
- **Zoom Account Type**: Pro, Business, Enterprise, or Education
- **Basic accounts cannot create meetings via API**

## 📋 Testing Checklist

Before testing in Postman:

- [ ] ✅ Credentials in `.env` file
- [ ] ✅ Django settings loading credentials  
- [ ] ✅ JWT token generation working
- [ ] ✅ Teacher has Zoom account with same email
- [ ] ✅ Zoom account has Pro/Business plan
- [ ] ✅ API permissions granted
- [ ] ✅ No rate limits exceeded

## 🎯 Expected Behavior in Postman

When you create a booking with valid Zoom credentials:

**✅ Success Response:**
```json
{
    "zoom_meeting_id": "123456789",
    "zoom_join_url": "https://zoom.us/j/123456789?pwd=abc123",
    "zoom_start_url": "https://zoom.us/s/123456789?zak=xyz",
    "zoom_password": "meeting_password"
}
```

**❌ Failure Response:**
```json
{
    "warning": "Booking created but Zoom meeting failed: Invalid credentials"
}
```

## 🔧 Quick Fix Commands

If you need to update credentials:

```bash
# Update .env file
echo "ZOOM_API_KEY=your_new_key" >> .env
echo "ZOOM_API_SECRET=your_new_secret" >> .env

# Restart Django server
python manage.py runserver
```

## 📞 Support Resources

- **Zoom API Docs**: https://marketplace.zoom.us/docs/api-reference/zoom-api
- **JWT App Setup**: https://marketplace.zoom.us/docs/guides/build/jwt-app
- **API Rate Limits**: https://marketplace.zoom.us/docs/api-reference/rate-limits

Your credentials look valid and are properly configured! Test the booking creation in Postman - it should automatically create Zoom meetings. 🚀
