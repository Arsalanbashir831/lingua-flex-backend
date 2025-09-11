# 🚀 Quick Postman Testing Guide - Fixed Endpoints

## 📋 Current Status
- ✅ Server running at `http://localhost:8000`
- ✅ Booking ID: **14** (use this integer ID, not UUID)
- ✅ Zoom meeting successfully created
- ✅ URL patterns fixed to use integer IDs

## 🎯 Endpoints to Test Now

### **1. Get Your Booking Details**
**Method:** `GET`
**URL:** `http://localhost:8000/api/bookings/bookings/14/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected:** Should return booking details with Zoom info

---

### **2. Get All Your Bookings**
**Method:** `GET`
**URL:** `http://localhost:8000/api/bookings/bookings/my/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected:** Array of your bookings including booking ID 14

---

### **3. Get Zoom Meeting Info**
**Method:** `GET`
**URL:** `http://localhost:8000/api/bookings/bookings/14/meeting_info/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
```
**Expected Response:**
```json
{
    "meeting_details": {
        "meeting_id": "85257371299",
        "join_url": "https://us05web.zoom.us/j/85257371299?pwd=zG3LecvIwDtxMjMuME7lwG3wa8mSBQ.1",
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
```

---

### **4. Test Reschedule Booking**
**Method:** `POST`
**URL:** `http://localhost:8000/api/bookings/bookings/14/reschedule/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "new_start_time": "2025-08-07T10:00:00Z",
    "new_end_time": "2025-08-07T11:00:00Z",
    "reason": "Testing reschedule functionality"
}
```
**Expected:** Success message with updated booking details

---

### **5. Test Cancel Booking**
**Method:** `POST`
**URL:** `http://localhost:8000/api/bookings/bookings/14/cancel/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Body (raw JSON):**
```json
{
    "reason": "Testing cancel functionality"
}
```
**Expected:** Success message with cancelled status

---

### **6. Create New Meeting (If Needed)**
**Method:** `POST`
**URL:** `http://localhost:8000/api/bookings/bookings/14/create_meeting/`
**Headers:**
```
Authorization: Bearer YOUR_STUDENT_ACCESS_TOKEN
Content-Type: application/json
```
**Expected:** New Zoom meeting details

---

## 🔧 Testing Steps

### Step 1: Test Current Booking
1. Use endpoint #1 to get booking details
2. Use endpoint #2 to verify it appears in your bookings list
3. Use endpoint #3 to get meeting info

### Step 2: Test Management
1. Use endpoint #4 to reschedule
2. Use endpoint #1 again to verify changes
3. Use endpoint #5 to cancel (optional - this will delete the booking)

### Step 3: Create New Booking
If you cancelled, create a new booking:
```json
{
    "teacher": "e3912742-f1dc-40ec-bcb2-e5f1f237fa61",
    "start_time": "2025-08-07T14:00:00Z",
    "end_time": "2025-08-07T15:00:00Z",
    "session_type": "video_call",
    "notes": "New test booking"
}
```

---

## 📝 Key Points

1. **Use Integer IDs:** Always use `14` (or whatever integer you get), not UUIDs
2. **Include Trailing Slash:** Use `/api/bookings/bookings/my/` (with slash)
3. **Check Headers:** Ensure `Authorization: Bearer TOKEN` is correct
4. **Use Full URLs:** Always include `http://localhost:8000`

---

## ✅ Success Indicators

- ✅ GET requests return 200 OK with data
- ✅ POST requests return 200 OK with success messages  
- ✅ Zoom URLs are present and clickable
- ✅ Booking statuses update correctly
- ✅ No 404 "Not Found" errors

---

## 🐛 If You Get Errors

**404 Not Found:**
- Check you're using integer ID (14), not UUID
- Verify URL has trailing slash where needed

**401 Unauthorized:**
- Get fresh token by logging in again
- Check `Authorization: Bearer TOKEN` format

**403 Forbidden:**
- Ensure you're using student token for student actions
- Use teacher token for teacher-only actions (like confirm)

---

## 🎯 Next: Test Teacher Actions

After testing student endpoints, login as teacher and test:
- `POST /api/bookings/bookings/14/confirm/` (teacher only)
- `GET /api/bookings/bookings/my/?role=teacher` (teacher's bookings)
