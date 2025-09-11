# 🎯 Zoom Meeting API Endpoints Guide

## 📋 Available Zoom Meeting Endpoints

### 1. **Create Zoom Meeting** (NEW!)
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/create_meeting/`

**Purpose:** Create or recreate a Zoom meeting for any booking

**Who can use:** Both students and teachers (for their bookings)

**Request:**
```http
POST {{base_url}}/api/bookings/bookings/{{booking_id}}/create_meeting/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response:**
```json
{
    "message": "Zoom meeting created successfully",
    "meeting_details": {
        "meeting_id": "83390305438",
        "join_url": "https://us05web.zoom.us/j/83390305438?pwd=...",
        "start_url": "https://us05web.zoom.us/s/83390305438?zak=...",
        "password": "ZLPA2y",
        "host_email": "teacher@example.com"
    },
    "booking": {
        "id": "booking_uuid",
        "zoom_meeting_id": "83390305438",
        "zoom_join_url": "https://us05web.zoom.us/j/83390305438?pwd=...",
        "zoom_start_url": "https://us05web.zoom.us/s/83390305438?zak=...",
        "zoom_password": "ZLPA2y",
        "status": "CONFIRMED"
    }
}
```

---

### 2. **Get Meeting Information**
**Endpoint:** `GET /api/bookings/bookings/{booking_id}/meeting_info/`

**Purpose:** Get Zoom meeting details for a booking

**Who can use:** Both students and teachers (for their bookings)

**Request:**
```http
GET {{base_url}}/api/bookings/bookings/{{booking_id}}/meeting_info/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
    "meeting_details": {
        "meeting_id": "83390305438",
        "join_url": "https://us05web.zoom.us/j/83390305438?pwd=...",
        "start_url": "https://us05web.zoom.us/s/83390305438?zak=...",
        "password": "ZLPA2y",
        "host_email": "teacher@example.com",
        "booking_id": "booking_uuid",
        "start_time": "2025-08-06T09:00:00Z",
        "end_time": "2025-08-06T10:00:00Z",
        "status": "CONFIRMED"
    }
}
```

---

### 3. **Confirm Booking** (Enhanced)
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/confirm/`

**Purpose:** Confirm a pending booking and automatically create Zoom meeting

**Who can use:** Teachers only

**Request:**
```http
POST {{base_url}}/api/bookings/bookings/{{booking_id}}/confirm/
Authorization: Bearer TEACHER_ACCESS_TOKEN
Content-Type: application/json
```

**Response:**
```json
{
    "message": "Booking confirmed successfully",
    "booking": {
        "id": "booking_uuid",
        "status": "CONFIRMED",
        "zoom_meeting_id": "83390305438",
        "zoom_join_url": "https://us05web.zoom.us/j/83390305438?pwd=...",
        "zoom_start_url": "https://us05web.zoom.us/s/83390305438?zak=...",
        "zoom_password": "ZLPA2y"
    }
}
```

---

### 4. **Reschedule Booking** (Enhanced)
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/reschedule/`

**Purpose:** Reschedule a booking and automatically update Zoom meeting

**Who can use:** Both students and teachers (for their bookings)

**Request:**
```http
POST {{base_url}}/api/bookings/bookings/{{booking_id}}/reschedule/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "new_start_time": "2025-08-06T14:00:00Z",
    "new_end_time": "2025-08-06T15:00:00Z",
    "reason": "Schedule conflict resolved"
}
```

**Response:**
```json
{
    "message": "Booking rescheduled successfully",
    "changes": {
        "old_start_time": "2025-08-06T09:00:00Z",
        "old_end_time": "2025-08-06T10:00:00Z",
        "new_start_time": "2025-08-06T14:00:00Z",
        "new_end_time": "2025-08-06T15:00:00Z",
        "reason": "Schedule conflict resolved"
    },
    "booking": {
        "id": "booking_uuid",
        "start_time": "2025-08-06T14:00:00Z",
        "end_time": "2025-08-06T15:00:00Z",
        "zoom_meeting_id": "83390305438",
        "zoom_join_url": "https://us05web.zoom.us/j/83390305438?pwd=..."
    }
}
```

---

### 5. **Cancel Booking** (Enhanced)
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/cancel/`

**Purpose:** Cancel a booking and automatically delete Zoom meeting

**Who can use:** Both students and teachers (for their bookings)

**Request:**
```http
POST {{base_url}}/api/bookings/bookings/{{booking_id}}/cancel/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "reason": "Personal emergency - need to cancel"
}
```

**Response:**
```json
{
    "message": "Booking cancelled successfully",
    "booking": {
        "id": "booking_uuid",
        "status": "CANCELLED",
        "cancellation_reason": "Personal emergency - need to cancel",
        "zoom_meeting_id": null,
        "zoom_join_url": null,
        "zoom_start_url": null,
        "zoom_password": null
    }
}
```

---

## 🎯 Common Use Cases

### **For Students:**
1. **Join a meeting:** Use `GET /meeting_info/` to get the join URL
2. **Request meeting creation:** Use `POST /create_meeting/` if no meeting exists
3. **Reschedule:** Use `POST /reschedule/` to change times

### **For Teachers:**
1. **Confirm and create meeting:** Use `POST /confirm/` for pending bookings
2. **Get start URL:** Use `GET /meeting_info/` to get the host start URL
3. **Recreate meeting:** Use `POST /create_meeting/` if needed
4. **Manage schedule:** Use `POST /reschedule/` or `POST /cancel/`

---

## 🔧 Error Handling

### **Common Errors:**
- **403 Forbidden:** User not authorized for this booking
- **404 Not Found:** Booking doesn't exist or no meeting associated
- **400 Bad Request:** Invalid data or booking state
- **500 Internal Server Error:** Zoom API issues

### **Example Error Response:**
```json
{
    "error": "Only the teacher or student can create meeting links for this booking"
}
```

---

## 📱 Postman Testing Order

1. **Login** as teacher/student
2. **Create booking** (if needed)
3. **Create meeting:** `POST /create_meeting/`
4. **Get meeting info:** `GET /meeting_info/`
5. **Test reschedule:** `POST /reschedule/`
6. **Test cancel:** `POST /cancel/`

---

## 🎉 Features

✅ **Automatic Zoom integration** - Real meetings created  
✅ **Both roles supported** - Students and teachers can manage  
✅ **Meeting lifecycle** - Create, update, delete automatically  
✅ **Error handling** - Comprehensive error responses  
✅ **Security** - Only booking participants can access  
✅ **Real URLs** - Clickable Zoom meeting links  

Your Zoom meeting integration is now complete with dedicated endpoints! 🚀
