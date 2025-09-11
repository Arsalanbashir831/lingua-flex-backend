# 🚀 Quick Test Guide - Zoom Meeting Endpoints

## 🎯 **NEW ENDPOINT: Create Meeting Link**

### **Main Endpoint for Students & Teachers:**
```http
POST {{base_url}}/api/bookings/bookings/{{booking_id}}/create_meeting/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**This endpoint will:**
✅ Create a real Zoom meeting  
✅ Return meeting ID, join URL, start URL, and password  
✅ Work for both students and teachers  
✅ Update the booking with Zoom details  

---

## 📋 **Step-by-Step Testing in Postman**

### **Step 1: Login and Create Booking**
1. Login as teacher → Get access token
2. Login as student → Get access token  
3. Create a booking → Get booking ID

### **Step 2: Create Zoom Meeting (NEW!)**
```http
POST http://localhost:8000/api/bookings/bookings/{booking_id}/create_meeting/
Authorization: Bearer STUDENT_OR_TEACHER_TOKEN
```

**Expected Response:**
```json
{
    "message": "Zoom meeting created successfully",
    "meeting_details": {
        "meeting_id": "83390305438",
        "join_url": "https://us05web.zoom.us/j/83390305438?pwd=...",
        "start_url": "https://us05web.zoom.us/s/83390305438?zak=...",
        "password": "ZLPA2y",
        "host_email": "teacher@example.com"
    }
}
```

### **Step 3: Get Meeting Info**
```http
GET http://localhost:8000/api/bookings/bookings/{booking_id}/meeting_info/
Authorization: Bearer YOUR_TOKEN
```

### **Step 4: Test Other Actions**
- **Reschedule:** Updates Zoom meeting time automatically
- **Cancel:** Deletes Zoom meeting automatically

---

## 🎯 **Use Cases**

### **For Students:**
```javascript
// Get meeting link to join class
GET /api/bookings/bookings/{booking_id}/meeting_info/
// Returns: join_url to click and join Zoom meeting
```

### **For Teachers:**
```javascript
// Get host link to start class
GET /api/bookings/bookings/{booking_id}/meeting_info/
// Returns: start_url to click and start Zoom meeting
```

### **For Both:**
```javascript
// Create meeting if doesn't exist
POST /api/bookings/bookings/{booking_id}/create_meeting/
// Creates: Real Zoom meeting with all details
```

---

## ✅ **Updated Postman Collection**

Your Postman collection now includes:
- ✅ **Create Zoom Meeting** - Main endpoint for meeting creation
- ✅ **Get Meeting Info** - Get meeting details and URLs
- ✅ **Enhanced Confirm** - Auto-creates meeting when confirming
- ✅ **Enhanced Reschedule** - Auto-updates meeting time
- ✅ **Enhanced Cancel** - Auto-deletes meeting

---

## 🎉 **Ready to Test!**

1. **Import updated Postman collection**
2. **Test the new `/create_meeting/` endpoint**
3. **Click the returned `join_url`** - it will open a real Zoom meeting!
4. **Both students and teachers** can create and access meetings

Your LinguaFlex platform now has **complete Zoom integration** with dedicated endpoints for both students and teachers! 🌟
