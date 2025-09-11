# 📋 Postman Test Data - Copy & Paste Ready

## 🎯 URLs for Testing (Replace booking_id with 14)

```
GET http://localhost:8000/api/bookings/bookings/14/
GET http://localhost:8000/api/bookings/bookings/my/
GET http://localhost:8000/api/bookings/bookings/14/meeting_info/
POST http://localhost:8000/api/bookings/bookings/14/reschedule/
POST http://localhost:8000/api/bookings/bookings/14/cancel/
POST http://localhost:8000/api/bookings/bookings/14/create_meeting/
```

## 🔑 Headers (Copy for all requests)

```
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
Content-Type: application/json
```

## 📝 JSON Bodies (Copy for POST requests)

### Reschedule Body:
```json
{
    "new_start_time": "2025-08-07T10:00:00Z",
    "new_end_time": "2025-08-07T11:00:00Z",
    "reason": "Testing reschedule functionality"
}
```

### Cancel Body:
```json
{
    "reason": "Testing cancel functionality"
}
```

### Create New Booking Body:
```json
{
    "teacher": "e3912742-f1dc-40ec-bcb2-e5f1f237fa61",
    "start_time": "2025-08-07T14:00:00Z", 
    "end_time": "2025-08-07T15:00:00Z",
    "session_type": "video_call",
    "notes": "New test booking"
}
```

## 🎯 Expected Status Codes

- GET requests: `200 OK`
- POST reschedule: `200 OK` 
- POST cancel: `200 OK`
- POST create_meeting: `200 OK`
- POST new booking: `201 Created`

## 📊 Sample Expected Responses

### GET Booking Details (200 OK):
```json
{
    "id": 14,
    "student_name": "Jane Student",
    "teacher_name": "John Jane", 
    "start_time": "2025-08-07T10:00:00Z",
    "end_time": "2025-08-07T11:00:00Z",
    "status": "CONFIRMED",
    "zoom_meeting_id": "85257371299",
    "zoom_join_url": "https://us05web.zoom.us/j/85257371299?pwd=...",
    "zoom_start_url": "https://us05web.zoom.us/s/85257371299?zak=...",
    "zoom_password": "T8jqxv"
}
```

### GET My Bookings (200 OK):
```json
[
    {
        "id": 14,
        "student_name": "Jane Student",
        "teacher_name": "John Jane",
        "start_time": "2025-08-07T10:00:00Z",
        "end_time": "2025-08-07T11:00:00Z",
        "status": "CONFIRMED",
        "zoom_meeting_id": "85257371299",
        "zoom_join_url": "https://us05web.zoom.us/j/85257371299?pwd=..."
    }
]
```

### POST Reschedule (200 OK):
```json
{
    "message": "Booking rescheduled successfully",
    "changes": {
        "old_start_time": "2025-08-06T09:00:00Z",
        "old_end_time": "2025-08-06T18:00:00Z", 
        "new_start_time": "2025-08-07T10:00:00Z",
        "new_end_time": "2025-08-07T11:00:00Z",
        "reason": "Testing reschedule functionality"
    },
    "booking": { /* updated booking object */ }
}
```

### POST Cancel (200 OK):
```json
{
    "message": "Booking cancelled successfully",
    "booking": {
        "id": 14,
        "status": "CANCELLED",
        "cancellation_reason": "Testing cancel functionality",
        "zoom_meeting_id": null,
        "zoom_join_url": null
    }
}
```
