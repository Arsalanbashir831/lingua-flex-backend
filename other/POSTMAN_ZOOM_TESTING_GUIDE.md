# Postman Testing Guide - Zoom Meeting API Endpoints

## Server Information
- **Base URL**: `http://localhost:8000`
- **API Base**: `http://localhost:8000/api/bookings/`

## Prerequisites
1. Django server running on `http://localhost:8000`
2. Valid user accounts (teachers and students)
3. Authentication tokens
4. Zoom API credentials configured in `.env`

## Authentication Setup

### 1. Get Authentication Token
**Endpoint**: `POST http://localhost:8000/api/login/`
**Body** (raw JSON):
```json
{
    "email": "teacher@example.com",
    "password": "your_password"
}
```
**Response**: Save the `access_token` for subsequent requests.

### 2. Set Authorization Header
For all subsequent requests, add:
- **Header**: `Authorization`
- **Value**: `Bearer YOUR_ACCESS_TOKEN`

## Zoom Meeting API Endpoints Testing

### 1. Teacher Availability Management

#### Create Teacher Availability
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/availability/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```
**Body** (raw JSON):
```json
{
    "date": "2025-08-06",
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "is_available": true
}
```

#### Get Available Slots
**Method**: `GET`
**URL**: `http://localhost:8000/api/bookings/slots/available/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**Query Parameters**:
- `teacher_id`: (optional) Filter by specific teacher
- `date`: (optional) Filter by specific date (YYYY-MM-DD)

#### Get Teacher Schedule
**Method**: `GET`
**URL**: `http://localhost:8000/api/bookings/schedule/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 2. Session Booking (With Zoom Integration)

#### Create Session Booking (Auto-creates Zoom Meeting)
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/bookings/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```
**Body** (raw JSON):
```json
{
    "teacher": "TEACHER_UUID",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "session_type": "video_call",
    "notes": "First language lesson"
}
```
**Expected Response**:
```json
{
    "id": "booking_uuid",
    "teacher": "teacher_uuid",
    "student": "student_uuid",
    "start_time": "2025-08-06T09:00:00Z",
    "end_time": "2025-08-06T10:00:00Z",
    "status": "confirmed",
    "zoom_meeting_id": "123456789",
    "zoom_join_url": "https://zoom.us/j/123456789",
    "zoom_start_url": "https://zoom.us/s/123456789",
    "zoom_password": "abc123",
    "session_type": "video_call",
    "notes": "First language lesson"
}
```

#### Get My Bookings
**Method**: `GET`
**URL**: `http://localhost:8000/api/bookings/bookings/my/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

#### Get Specific Booking Details
**Method**: `GET`
**URL**: `http://localhost:8000/api/bookings/bookings/{booking_id}/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

#### Confirm Booking
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/bookings/{booking_id}/confirm/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

#### Cancel Booking (Deletes Zoom Meeting)
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/bookings/{booking_id}/cancel/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```
**Body** (raw JSON):
```json
{
    "reason": "Personal emergency"
}
```

#### Reschedule Booking (Updates Zoom Meeting)
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/bookings/{booking_id}/reschedule/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```
**Body** (raw JSON):
```json
{
    "new_start_time": "2025-08-06T14:00:00Z",
    "new_end_time": "2025-08-06T15:00:00Z",
    "reason": "Schedule conflict resolved"
}
```

### 3. Session Feedback

#### Create Session Feedback
**Method**: `POST`
**URL**: `http://localhost:8000/api/bookings/feedback/`
**Headers**: 
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```
**Body** (raw JSON):
```json
{
    "session": "SESSION_BOOKING_UUID",
    "rating": 5,
    "comments": "Excellent session! Very helpful.",
    "areas_for_improvement": "More focus on pronunciation"
}
```

## Testing Scenarios

### Scenario 1: Complete Booking Flow
1. **Login as Teacher** → Get token
2. **Create Availability** → POST availability slots
3. **Login as Student** → Get token
4. **View Available Slots** → GET available slots
5. **Book Session** → POST booking (creates Zoom meeting)
6. **View Booking Details** → GET booking (see Zoom details)
7. **Join Meeting** → Use zoom_join_url

### Scenario 2: Booking Management
1. **Create Booking** → POST booking
2. **Reschedule** → POST reschedule (updates Zoom meeting)
3. **Cancel** → POST cancel (deletes Zoom meeting)

### Scenario 3: Feedback Flow
1. **Complete Session** → Simulate session completion
2. **Submit Feedback** → POST feedback

## Expected Zoom Integration Behavior

### When Creating a Booking:
- Zoom meeting is automatically created
- Response includes:
  - `zoom_meeting_id`
  - `zoom_join_url` (for students)
  - `zoom_start_url` (for teachers/hosts)
  - `zoom_password` (if required)

### When Rescheduling:
- Existing Zoom meeting is updated with new time
- Meeting URLs remain the same
- Participants get updated meeting details

### When Canceling:
- Zoom meeting is deleted
- Meeting URLs become invalid

## Error Scenarios to Test

### 1. Invalid Zoom Credentials
**Expected**: Error message about Zoom API credentials

### 2. Conflicting Time Slots
**Expected**: Validation error for overlapping bookings

### 3. Past Date Booking
**Expected**: Validation error for past dates

### 4. Unauthorized Access
**Expected**: 401 Unauthorized for missing/invalid tokens

## Environment Variables to Check
Ensure these are set in your `.env`:
```
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret
```

## Common Response Codes
- `200`: Success (GET requests)
- `201`: Created successfully (POST requests)
- `204`: Updated successfully (PUT/PATCH requests)
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (permission denied)
- `404`: Not Found
- `500`: Server Error (check Zoom credentials)

## Tips for Testing
1. Use real future dates and times
2. Test with different user roles (teacher vs student)
3. Verify Zoom meeting creation in Zoom dashboard
4. Test edge cases (past dates, conflicts, etc.)
5. Check that cancelled meetings are properly deleted
6. Verify rescheduled meetings update correctly

## Debugging
If you encounter issues:
1. Check Django server logs
2. Verify Zoom API credentials
3. Ensure user has proper permissions
4. Check authentication tokens
5. Validate request data format
