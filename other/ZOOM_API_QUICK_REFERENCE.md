# 📋 Quick Reference - Zoom API Endpoints & Sample Data

## 🔗 Base URL
```
http://localhost:8000
```

## 🚀 Quick Test Sequence

### 1. LOGIN AS TEACHER
```
POST /api/login/
Content-Type: application/json

{
    "email": "teacher@example.com",
    "password": "your_password"
}
```
**Save:** `access_token` and `user.id`

### 2. LOGIN AS STUDENT  
```
POST /api/login/
Content-Type: application/json

{
    "email": "student@example.com", 
    "password": "your_password"
}
```
**Save:** `access_token` and `user.id`

### 3. CREATE TEACHER AVAILABILITY
```
POST /api/bookings/availability/
Authorization: Bearer TEACHER_TOKEN
Content-Type: application/json

{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_recurring": true
}
```

### 4. 🎯 CREATE BOOKING WITH ZOOM (MAIN TEST)
```
POST /api/bookings/bookings/
Authorization: Bearer STUDENT_TOKEN
Content-Type: application/json

{
    "teacher": "TEACHER_UUID_HERE",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "session_type": "video_call",
    "notes": "Testing Zoom integration"
}
```
**Expected:** Response includes `zoom_meeting_id`, `zoom_join_url`, `zoom_start_url`

### 5. GET BOOKING DETAILS
```
GET /api/bookings/bookings/{BOOKING_ID}/
Authorization: Bearer STUDENT_TOKEN
```

### 6. RESCHEDULE BOOKING (UPDATES ZOOM)
```
POST /api/bookings/bookings/{BOOKING_ID}/reschedule/
Authorization: Bearer STUDENT_TOKEN
Content-Type: application/json

{
    "new_start_time": "2025-08-06T14:00:00Z",
    "new_end_time": "2025-08-06T15:00:00Z",
    "reason": "Schedule change"
}
```

### 7. CANCEL BOOKING (DELETES ZOOM)
```
POST /api/bookings/bookings/{BOOKING_ID}/cancel/
Authorization: Bearer STUDENT_TOKEN
Content-Type: application/json

{
    "reason": "Need to cancel"
}
```

## 📋 All Available Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/login/` | User login | No |
| POST | `/api/bookings/availability/` | Create teacher availability | Teacher |
| GET | `/api/bookings/slots/available/` | Get available slots | Student |
| GET | `/api/bookings/schedule/` | Get teacher schedule | Teacher |
| POST | `/api/bookings/bookings/` | **Create booking + Zoom meeting** | Student |
| GET | `/api/bookings/bookings/my/` | Get user's bookings | Any |
| GET | `/api/bookings/bookings/{id}/` | Get booking details | Owner |
| POST | `/api/bookings/bookings/{id}/confirm/` | Confirm booking | Teacher |
| POST | `/api/bookings/bookings/{id}/reschedule/` | **Reschedule + Update Zoom** | Owner |
| POST | `/api/bookings/bookings/{id}/cancel/` | **Cancel + Delete Zoom** | Owner |
| POST | `/api/bookings/feedback/` | Create session feedback | Any |

## 🎯 Test Cases for Postman

### Test Case 1: Basic Zoom Integration
```json
{
    "teacher": "{{teacher_id}}",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "session_type": "video_call",
    "notes": "Basic Zoom test"
}
```

### Test Case 2: Extended Session
```json
{
    "teacher": "{{teacher_id}}",
    "start_time": "2025-08-07T14:00:00Z", 
    "end_time": "2025-08-07T16:00:00Z",
    "session_type": "video_call",
    "notes": "2-hour extended session"
}
```

### Test Case 3: Multiple Bookings
```json
{
    "teacher": "{{teacher_id}}",
    "start_time": "2025-08-08T10:30:00Z",
    "end_time": "2025-08-08T11:30:00Z", 
    "session_type": "video_call",
    "notes": "Multiple booking test"
}
```

## ✅ Success Criteria

**✅ Booking Creation:**
- Returns 201 Created
- Response includes `zoom_meeting_id`
- Response includes `zoom_join_url` 
- Response includes `zoom_start_url`
- Status is "CONFIRMED"

**✅ Zoom URLs:**
- `zoom_join_url` starts with "https://zoom.us/j/"
- `zoom_start_url` starts with "https://zoom.us/s/"
- URLs are clickable and functional

**✅ Reschedule:**
- Returns 200 OK
- Booking times updated
- Same `zoom_meeting_id` (meeting updated, not recreated)

**✅ Cancel:**
- Returns 200 OK
- Status changed to "CANCELLED"
- `zoom_meeting_id` set to null
- `zoom_join_url` set to null

## 🚨 Common Issues & Solutions

**Issue:** No Zoom meeting created
**Solution:** Check `.env` file for `ZOOM_API_KEY` and `ZOOM_API_SECRET`

**Issue:** 401 Unauthorized
**Solution:** Add `Authorization: Bearer YOUR_TOKEN` header

**Issue:** 400 Bad Request  
**Solution:** Use future dates, valid teacher UUID, correct time format

**Issue:** Teacher not found
**Solution:** Ensure teacher UUID is correct and user has TEACHER role

## 📞 Support

If Zoom meetings aren't being created:
1. Check server logs for errors
2. Verify Zoom API credentials
3. Ensure teacher email is associated with Zoom account
4. Test with simple booking first

**🎯 Goal:** Successfully create a booking that generates a real, joinable Zoom meeting!
