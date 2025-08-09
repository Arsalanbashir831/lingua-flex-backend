# 🎯 Zoom App Scopes Configuration Guide

## ✅ Progress So Far
- ✅ **OAuth Authentication Working**: Access token obtained successfully
- ✅ **Credentials Valid**: Server-to-Server OAuth flow successful
- ❌ **Missing Scopes**: App needs additional permissions

## 🔧 Required Scopes for LinguaFlex

Your Zoom app needs these scopes to work with our booking system:

### **Essential Scopes:**
```
meeting:write        - Create meetings
meeting:read         - Read meeting details  
meeting:update       - Update meetings
meeting:delete       - Delete meetings
user:read            - Read user information
user:read:admin      - Read user details (admin level)
```

### **Optional but Recommended:**
```
webinar:write        - Create webinars (future feature)
webinar:read         - Read webinar info
recording:read       - Access recordings
dashboard:read       - Access usage dashboards
```

## 🚀 How to Add Scopes to Your Zoom App

### **Step 1: Access Your App**
1. Go to: https://marketplace.zoom.us/develop/apps
2. Find your app: **"LinguaFlex"** or similar
3. Click **"Manage"**

### **Step 2: Configure Scopes**
1. Click **"Scopes"** tab
2. Add these scopes:
   - ✅ `meeting:write`
   - ✅ `meeting:read` 
   - ✅ `meeting:update`
   - ✅ `meeting:delete`
   - ✅ `user:read`
   - ✅ `user:read:admin`

### **Step 3: Activate App**
1. Click **"Activation"** tab
2. **Activate** your app if not already active
3. **Save changes**

## 🧪 Test After Scope Update

Run this command to test:
```bash
python test_zoom_oauth.py
```

**Expected Success Output:**
```
✅ Access token obtained successfully!
✅ User info retrieved successfully!
✅ Meeting created successfully!
✅ Meeting deleted successfully!
✅ All tests passed!
```

## 🎯 Alternative: Create New App with Correct Scopes

If you can't modify the existing app:

### **Quick New App Setup:**
1. **Go to**: https://marketplace.zoom.us/develop/create
2. **Choose**: "Server-to-Server OAuth" 
3. **App Info**:
   ```
   App Name: LinguaFlex Meetings
   App Type: Server-to-Server OAuth
   Company: [Your Company]
   ```
4. **Add All Required Scopes** (list above)
5. **Activate App**
6. **Copy New Credentials** to `.env`

## 📋 Verify App Type

Make sure your app is **"Server-to-Server OAuth"** not:
- ❌ JWT (deprecated)
- ❌ OAuth (user-level)
- ❌ Webhook-only

## 🔄 After Fixing Scopes

1. **Test credentials**: `python test_zoom_oauth.py`
2. **Restart Django server**: Server will pick up new working credentials  
3. **Test in Postman**: Create bookings with automatic Zoom meetings
4. **Verify integration**: Check that booking responses include Zoom URLs

## 🚨 Common Issues

**Issue**: "Invalid access token" errors
**Solution**: Make sure app is **activated** and has all required scopes

**Issue**: "User not found" errors  
**Solution**: Add `user:read:admin` scope

**Issue**: "Insufficient privileges"
**Solution**: Ensure Zoom account is Pro/Business/Enterprise (not Basic)

## ✅ Success Indicators

When scopes are configured correctly:
- ✅ `test_zoom_oauth.py` passes all tests
- ✅ Django booking endpoints create real Zoom meetings
- ✅ Postman responses include `zoom_join_url`, `zoom_meeting_id`
- ✅ Zoom meetings are actually joinable

## 🎯 Next Steps

1. **Add scopes** to your Zoom app
2. **Test with** `python test_zoom_oauth.py`  
3. **Restart Django** server
4. **Test booking creation** in Postman
5. **Join a real Zoom meeting** created by the API

The authentication is working - we just need the right permissions! 🚀
