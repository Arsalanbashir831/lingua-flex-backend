# 🔧 Zoom Credentials Setup Guide

## ❌ Current Issue
Your Zoom API credentials are invalid/expired:
```
Error: "Invalid access token" (Code 124)
```

## 🚀 Quick Fix Options

### **Option 1: Get New Zoom Credentials (5 minutes)**

1. **Visit Zoom Marketplace**: https://marketplace.zoom.us/develop/create
2. **Click "Create"** → **"JWT App"**
3. **Fill Basic Information**:
   - App Name: `LinguaFlex Booking System`
   - Company Name: Your company
   - Developer Email: Your email
4. **Get Credentials** from "App Credentials" section
5. **Update `.env` file**:
   ```env
   ZOOM_API_KEY=your_new_api_key_here
   ZOOM_API_SECRET=your_new_api_secret_here
   ZOOM_ACCOUNT_ID=your_account_id_here
   ```
6. **Restart Django server**

### **Option 2: Test Without Zoom (Immediate)**

Test the booking system without Zoom integration first:

1. **Booking will work** - just no Zoom meetings created
2. **All other features** work normally
3. **Add Zoom later** when you have valid credentials

## 📋 Zoom App Requirements

When creating the JWT app, ensure:

- **App Type**: JWT (not OAuth)
- **Account Type**: Pro/Business/Enterprise (Basic won't work)
- **Scopes Needed**:
  - `meeting:write` - Create meetings
  - `meeting:read` - Read meeting info
  - `meeting:update` - Update meetings
  - `meeting:delete` - Delete meetings

## 🧪 Test New Credentials

After updating `.env`, run:
```bash
python test_zoom_credentials.py
```

Expected output:
```
✅ Zoom API connection successful!
✅ Account can create meetings via API
✅ Test meeting created successfully!
```

## 🎯 Postman Testing Options

### **With Valid Zoom Credentials:**
- Bookings automatically create Zoom meetings
- Response includes `zoom_join_url`, `zoom_meeting_id`, etc.

### **Without Zoom (Current State):**
- Bookings work normally
- No Zoom fields in response
- System shows warning message

Both options allow you to test the booking API functionality!

## 🔗 Helpful Links

- **Zoom JWT App**: https://marketplace.zoom.us/develop/create
- **Zoom API Docs**: https://marketplace.zoom.us/docs/api-reference/zoom-api
- **JWT vs OAuth**: https://marketplace.zoom.us/docs/guides/build/jwt-app

## ⚡ Quick Decision

**Want to test immediately?** → Use Option 2 (test without Zoom)
**Want full Zoom integration?** → Use Option 1 (create new JWT app)

Either way, your booking system will work in Postman! 🚀
