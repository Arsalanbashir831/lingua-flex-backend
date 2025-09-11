# 🚀 Complete Postman Testing Guide - Zoom Meeting API

## 📋 Prerequisites

### 1. Server Setup
- ✅ Server running at: `http://localhost:8000`
- ✅ Database migrations applied
- ✅ Zoom credentials in `.env` file
- ✅ **Zoom scopes configured and tested successfully!**

### 2. Test Accounts Required
You'll need at least one teacher and one student account. If you don't have them, create using the registration endpoints first.

### 3. Postman Collection
Import the `LinguaFlex_Zoom_API.postman_collection.json` file into Postman.

---

## 🎯 Step-by-Step Testing Guide

### **STEP 1: Authentication**

#### 1.1 Login as Teacher
**Endpoint:** `POST http://localhost:8000/api/login/`
**Headers:**
```
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "email": "teacher@example.com",
    "password": "your_password"
}
```
**Expected Response:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "teacher_uuid_here",
        "email": "teacher@example.com",
        "role": "TEACHER",
        "full_name": "John Doe"
    }
}
```
**📝 Save:** Copy the `access_token` and `user.id` for subsequent requests.

#### 1.2 Login as Student
**Endpoint:** `POST http://localhost:8000/api/login/`
**Body (raw JSON):**
```json
{
    "email": "student@example.com",
    "password": "your_password"
}
```
**📝 Save:** Copy the student's `access_token` and `user.id`.

---

### **STEP 2: Create Teacher Availability**

#### 2.1 Set Teacher Availability
**Endpoint:** `POST http://localhost:8000/api/bookings/availability/`
**Headers:**
```
Authorization: Bearer YOUR_TEACHER_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_recurring": true
}
```
**Expected Response:**
```json
{
    "id": "availability_uuid",
    "teacher": "teacher_uuid",
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_recurring": true,
    "date": null
}
```

---

### **STEP 3: Create Session Booking (🎯 Main Zoom Test)**

#### 3.1 Create Booking with Zoom Meeting
**Endpoint:** `POST http://localhost:8000/api/bookings/bookings/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "teacher": "teacher_uuid_from_step_1",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "session_type": "video_call",
    "notes": "First language lesson - Testing Zoom integration"
}
```

**🎯 Expected Response (WITH ZOOM INTEGRATION):**
```json
{
    "id": "booking_uuid_here",
    "student": "student_uuid",
    "teacher": "teacher_uuid",
    "student_name": "Jane Smith",
    "teacher_name": "John Doe",
    "student_email": "student@example.com",
    "teacher_email": "teacher@example.com",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "duration_minutes": 60,
    "status": "CONFIRMED",
    "zoom_meeting_id": "123456789",
    "zoom_join_url": "https://zoom.us/j/123456789?pwd=abcdef",
    "zoom_start_url": "https://zoom.us/s/123456789?zak=xyz",
    "zoom_password": "abc123",
    "notes": "First language lesson - Testing Zoom integration",
    "cancellation_reason": "",
    "created_at": "2025-08-05T16:20:00Z",
    "updated_at": "2025-08-05T16:20:00Z",
    "can_cancel": true,
    "can_reschedule": true
}
```

**✅ Success Indicators:**
- `zoom_meeting_id` is present and not null
- `zoom_join_url` contains a valid Zoom meeting link
- `zoom_start_url` is provided for the teacher
- Status is `CONFIRMED` (automatically)

**📝 Save:** Copy the `booking_id` from the response.

---

### **STEP 4: Verify Booking Details**

#### 4.1 Get Booking Details
**Endpoint:** `GET http://localhost:8000/api/bookings/bookings/{booking_id}/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Note:** Use the integer `booking_id` from the response (e.g., 14), not a UUID.

#### 4.2 Get My Bookings  
**Endpoint:** `GET http://localhost:8000/api/bookings/bookings/my/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected Response:** Array containing your bookings with Zoom details.

#### 4.3 Get Meeting Information
**Endpoint:** `GET http://localhost:8000/api/bookings/bookings/{booking_id}/meeting_info/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected Response:**
```json
{
    "meeting_details": {
        "meeting_id": "85257371299",
        "join_url": "https://us05web.zoom.us/j/85257371299?pwd=...",
        "start_url": "https://us05web.zoom.us/s/85257371299?zak=...",
        "password": "T8jqxv",
        "host_email": "teacher@example.com",
        "participant_email": "student@example.com"
    },
    "booking_details": {
        "booking_id": 14,
        "start_time": "2025-08-06T09:00:00Z",
        "end_time": "2025-08-06T18:00:00Z",
        "status": "CONFIRMED"
    }
}
**Expected Response:** Same as Step 3.1 with all Zoom details intact.

#### 4.2 Get My Bookings
**Endpoint:** `GET http://localhost:8000/api/bookings/bookings/my/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected Response:** Array containing your booking with Zoom details.

---

### **STEP 5: Test Booking Management (Zoom Updates)**

#### 5.1 Reschedule Booking (Updates Zoom Meeting)
**Endpoint:** `POST http://localhost:8000/api/bookings/bookings/{booking_id}/reschedule/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "new_start_time": "2025-08-06T14:00:00Z",
    "new_end_time": "2025-08-06T15:00:00Z",
    "reason": "Schedule conflict resolved"
}
```
**Expected Response:**
```json
{
    "message": "Booking rescheduled successfully",
    "changes": {
        "old_start_time": "2025-08-06T09:00:00Z",
        "old_end_time": "2025-08-06T18:00:00Z",
        "new_start_time": "2025-08-06T14:00:00Z",
        "new_end_time": "2025-08-06T15:00:00Z",
        "reason": "Schedule conflict resolved"
    },
    "booking": {
        "id": 14,
        "start_time": "2025-08-06T14:00:00Z",
        "end_time": "2025-08-06T15:00:00Z",
        "zoom_meeting_id": "85257371299",
        "zoom_join_url": "https://us05web.zoom.us/j/85257371299?pwd=...",
        // ... other fields
    }
}
```

#### 5.2 Cancel Booking (Deletes Zoom Meeting)
**Endpoint:** `POST http://localhost:8000/api/bookings/bookings/{booking_id}/cancel/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "reason": "Personal emergency - need to cancel"
}
```
**Expected Response:**
```json
{
    "message": "Booking cancelled successfully",
    "booking": {
        "id": 14,
        "status": "CANCELLED",
        "cancellation_reason": "Personal emergency - need to cancel",
        "zoom_meeting_id": null,
        "zoom_join_url": null
        // ... other fields
    }
}
```

#### 5.3 Create Meeting Link (If Missing)
**Endpoint:** `POST http://localhost:8000/api/bookings/bookings/{booking_id}/create_meeting/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Expected Response:**
```json
{
    "message": "Zoom meeting created successfully",
    "zoom_meeting_id": "85257371299",
    "zoom_join_url": "https://us05web.zoom.us/j/85257371299?pwd=...",
    "zoom_start_url": "https://us05web.zoom.us/s/85257371299?zak=...",
    "zoom_password": "T8jqxv"
}
```

---

### **STEP 6: Test Session Feedback**

#### 6.1 Create Session Feedback
**Endpoint:** `POST http://localhost:8000/api/bookings/feedback/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "booking": "booking_uuid_from_step_3",
    "rating": 5,
    "comment": "Excellent session! Very helpful and engaging.",
    "is_from_student": true
}
```

---

## 🔧 Troubleshooting Guide

### **Issue 1: No Zoom Meeting Created**
**Symptoms:** Response doesn't include `zoom_meeting_id`
**Solutions:**
1. ✅ **RESOLVED:** Zoom OAuth scopes are now properly configured
2. Check `.env` file has valid Zoom credentials:
   ```
   ZOOM_ACCOUNT_ID=ZJmI_gxfSoqVY84zdfzaEA
   ZOOM_CLIENT_ID=8t0mzl52Sc...
   ZOOM_CLIENT_SECRET=VIyA2trx4Z...
   ```
3. ✅ **VERIFIED:** Zoom API connection working - test passed
4. Check server logs for any remaining errors

### **Issue 2: "Not Found" Errors**
**Symptoms:** 404 responses for booking details or my bookings
**Solutions:**
1. ✅ **FIXED:** Updated URL patterns to use integer IDs instead of UUIDs
2. Use the correct booking ID from create response (e.g., 14, not a UUID)
3. Verify endpoints:
   - `GET /api/bookings/bookings/my/` (note the trailing slash)
   - `GET /api/bookings/bookings/14/` (use integer ID)
4. Check authentication token is valid

### **Issue 3: Validation Errors**
**Symptoms:** 400 Bad Request responses
**Solutions:**
1. Use future dates only (not past dates)
2. Ensure teacher_id exists and user is a teacher
3. Check time format: `YYYY-MM-DDTHH:MM:SSZ`

---

## 📊 Expected Test Results

### **Successful Zoom Integration Flow:**
1. ✅ Teacher login → Get token
2. ✅ Student login → Get token  
3. ✅ Create availability → 201 Created
4. ✅ Create booking → 201 Created + Zoom meeting details
5. ✅ Get booking → 200 OK + Zoom details present
6. ✅ Reschedule → 200 OK + Updated Zoom meeting
7. ✅ Cancel → 200 OK + Zoom meeting deleted

### **Key Zoom Integration Points:**
- **Automatic Creation:** Zoom meeting created when booking is made
- **Real URLs:** `zoom_join_url` should be clickable Zoom links
- **Meeting IDs:** `zoom_meeting_id` should be valid Zoom meeting IDs
- **Updates:** Rescheduling updates the existing Zoom meeting
- **Cleanup:** Canceling deletes the Zoom meeting

---

## 🎯 Sample Test Data Sets

### **Test Set 1: Basic Booking**
```json
{
    "teacher": "replace_with_teacher_uuid",
    "start_time": "2025-08-07T10:00:00Z",
    "end_time": "2025-08-07T11:00:00Z",
    "session_type": "video_call",
    "notes": "Basic test booking"
}
```

### **Test Set 2: Extended Session**
```json
{
    "teacher": "replace_with_teacher_uuid",
    "start_time": "2025-08-08T14:00:00Z",
    "end_time": "2025-08-08T16:00:00Z",
    "session_type": "video_call",
    "notes": "Extended 2-hour session"
}
```

### **Test Set 3: Next Day Booking**
```json
{
    "teacher": "replace_with_teacher_uuid",
    "start_time": "2025-08-09T09:30:00Z",
    "end_time": "2025-08-09T10:30:00Z",
    "session_type": "video_call",
    "notes": "Early morning session"
}
```

---

## ✅ Testing Checklist

- [ ] Teacher and student accounts exist
- [ ] Server running at localhost:8000
- [ ] Postman collection imported
- [ ] Zoom credentials configured
- [ ] Teacher login successful
- [ ] Student login successful
- [ ] Teacher availability created
- [ ] Booking created with Zoom meeting
- [ ] Zoom URLs are valid and clickable
- [ ] Booking details show Zoom info
- [ ] Reschedule updates Zoom meeting
- [ ] Cancel removes Zoom meeting
- [ ] Feedback submission works

**🎉 Success Criteria:** When you create a booking, you should receive a response with valid `zoom_join_url` that you can actually click and join a real Zoom meeting!

---

## 🚀 ZOOM INTEGRATION STATUS: ✅ READY!

**✅ Integration Test Results:**
- ✅ Zoom OAuth Server-to-Server authentication working
- ✅ Access token generation successful
- ✅ User info retrieval working
- ✅ Meeting creation tested and verified
- ✅ Meeting deletion tested and verified
- ✅ All required scopes properly configured

**🎯 Your Zoom integration is now fully functional and ready for Postman testing!**

### Quick Start Testing:
1. **Start Django server:** `python manage.py runserver`
2. **Open Postman** and import the collection
3. **Follow Step 1-3** in this guide to create a booking
4. **Verify** you receive real Zoom meeting URLs in the response

Your bookings will now automatically create real Zoom meetings! 🎉
