# Zoom Meeting Booking System - API Documentation

## Overview
This system allows students to request meeting slots with teachers, and automatically creates Zoom meetings when teachers confirm the bookings.

## Prerequisites

### 1. Zoom API Configuration
Add these settings to your `.env` file:
```
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret
```

### 2. Dependencies
Make sure you have the required packages:
```bash
pip install PyJWT requests
```

## Authentication
All endpoints require authentication using Bearer token:
```
Authorization: Bearer <your_supabase_token>
```

## API Endpoints

### 1. Teacher Availability Management

#### Create Availability Slot (Teachers Only)
**POST** `/api/bookings/availability/`

**Request Body:**
```json
{
    "day_of_week": 1,  // 0=Monday, 1=Tuesday, etc.
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "is_recurring": true,
    "date": null  // Only for non-recurring slots
}
```

#### Get Available Time Slots
**GET** `/api/bookings/slots/available/?teacher_id=<uuid>&date=2025-01-15&duration=60`

**Query Parameters:**
- `teacher_id` (required): UUID of the teacher
- `date` (required): Date in YYYY-MM-DD format
- `duration` (optional): Session duration in minutes (default: 60)

**Response:**
```json
{
    "date": "2025-01-15",
    "teacher_id": "uuid-string",
    "available_slots": [
        {
            "start_time": "09:00",
            "end_time": "10:00",
            "datetime_start": "2025-01-15T09:00:00",
            "datetime_end": "2025-01-15T10:00:00"
        },
        {
            "start_time": "10:30",
            "end_time": "11:30",
            "datetime_start": "2025-01-15T10:30:00",
            "datetime_end": "2025-01-15T11:30:00"
        }
    ]
}
```

#### Get Teacher Schedule
**GET** `/api/bookings/schedule/?teacher_id=<uuid>&start_date=2025-01-15&end_date=2025-01-22`

**Response:**
```json
{
    "teacher_id": "uuid-string",
    "start_date": "2025-01-15",
    "end_date": "2025-01-22",
    "bookings": [
        {
            "start_time": "2025-01-15T09:00:00Z",
            "end_time": "2025-01-15T10:00:00Z",
            "status": "CONFIRMED",
            "student__first_name": "John",
            "student__last_name": "Doe"
        }
    ]
}
```

### 2. Session Booking Management

#### Create Booking Request (Students Only)
**POST** `/api/bookings/bookings/`

**Request Body:**
```json
{
    "teacher_id": "uuid-string",
    "start_time": "2025-01-15T09:00:00Z",
    "duration": 60,
    "notes": "Looking forward to practicing Spanish conversation"
}
```

**Response:**
```json
{
    "id": "booking-uuid",
    "student": "student-uuid",
    "teacher": "teacher-uuid",
    "student_name": "John Doe",
    "teacher_name": "Maria Garcia",
    "start_time": "2025-01-15T09:00:00Z",
    "end_time": "2025-01-15T10:00:00Z",
    "duration_minutes": 60,
    "status": "PENDING",
    "zoom_meeting_id": null,
    "zoom_join_url": null,
    "notes": "Looking forward to practicing Spanish conversation",
    "can_cancel": true,
    "can_reschedule": true,
    "zoom_info": {
        "meeting_id": null,
        "join_url": null,
        "has_meeting": false
    }
}
```

#### Confirm Booking and Create Zoom Meeting (Teachers Only)
**POST** `/api/bookings/bookings/<booking_id>/confirm/`

**Response:**
```json
{
    "message": "Booking confirmed and Zoom meeting created",
    "booking": {
        "id": "booking-uuid",
        "status": "CONFIRMED",
        "zoom_meeting_id": "123456789",
        "zoom_join_url": "https://zoom.us/j/123456789",
        "zoom_info": {
            "meeting_id": "123456789",
            "join_url": "https://zoom.us/j/123456789",
            "has_meeting": true
        }
    },
    "zoom_info": {
        "join_url": "https://zoom.us/j/123456789",
        "meeting_id": "123456789",
        "password": "meeting_password"
    }
}
```

#### Cancel Booking
**POST** `/api/bookings/bookings/<booking_id>/cancel/`

**Request Body:**
```json
{
    "reason": "Schedule conflict"
}
```

**Response:**
```json
{
    "message": "Booking cancelled successfully",
    "booking": {
        "id": "booking-uuid",
        "status": "CANCELLED",
        "cancellation_reason": "Schedule conflict"
    }
}
```

#### Reschedule Booking
**POST** `/api/bookings/bookings/<booking_id>/reschedule/`

**Request Body:**
```json
{
    "start_time": "2025-01-16T10:00:00Z",
    "duration": 60
}
```

#### Get My Bookings
**GET** `/api/bookings/bookings/my/?status=PENDING&role=student`

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, CONFIRMED, CANCELLED, COMPLETED)
- `role` (optional): Filter by role (student, teacher)

### 3. Session Feedback

#### Create Feedback (After Completed Session)
**POST** `/api/bookings/feedback/`

**Request Body:**
```json
{
    "booking_id": "booking-uuid",
    "rating": 5,
    "comment": "Excellent session! Very helpful teacher."
}
```

## Booking Flow

### For Students:
1. **Browse Teachers**: Get list of available teachers
2. **Check Availability**: `GET /api/bookings/slots/available/`
3. **Create Booking**: `POST /api/bookings/bookings/`
4. **Wait for Confirmation**: Teacher will confirm and create Zoom meeting
5. **Join Session**: Use the Zoom link provided
6. **Provide Feedback**: After session completion

### For Teachers:
1. **Set Availability**: `POST /api/bookings/availability/`
2. **Review Requests**: `GET /api/bookings/bookings/my/?role=teacher`
3. **Confirm Bookings**: `POST /api/bookings/bookings/<id>/confirm/`
4. **Conduct Session**: Use Zoom meeting link
5. **Mark Complete**: Update booking status

## Zoom Integration Features

### Automatic Meeting Creation
- When teacher confirms a booking, a Zoom meeting is automatically created
- Meeting details include both participant names
- Meeting duration matches the booked session time

### Meeting Management
- Meetings are automatically updated when sessions are rescheduled
- Meetings are deleted when sessions are cancelled
- Each booking stores the Zoom meeting ID and join URL

### Security Features
- Only the teacher and student can access meeting details
- Meetings are configured with appropriate security settings
- Waiting room can be enabled for additional security

## Error Handling

### Common Error Responses

**400 Bad Request**
```json
{
    "error": "Time slot is not available"
}
```

**403 Forbidden**
```json
{
    "error": "Only teachers can confirm bookings"
}
```

**404 Not Found**
```json
{
    "error": "Teacher not found"
}
```

**500 Internal Server Error**
```json
{
    "error": "Failed to create Zoom meeting: [details]"
}
```

## Status Workflow

```
PENDING → CONFIRMED → COMPLETED
    ↓
CANCELLED
```

- **PENDING**: Booking requested by student, awaiting teacher confirmation
- **CONFIRMED**: Teacher confirmed, Zoom meeting created
- **COMPLETED**: Session finished (can be manually updated)
- **CANCELLED**: Booking cancelled by either party

## Testing

### 1. Set Up Test Environment
```bash
# Install dependencies
pip install PyJWT requests

# Configure Zoom API (get from Zoom Marketplace)
ZOOM_API_KEY=your_test_api_key
ZOOM_API_SECRET=your_test_api_secret
```

### 2. Test Booking Flow
```python
# Example test script
import requests

# 1. Student checks availability
response = requests.get(
    "http://localhost:8000/api/bookings/slots/available/",
    params={"teacher_id": "teacher-uuid", "date": "2025-01-15"},
    headers={"Authorization": "Bearer student-token"}
)

# 2. Student creates booking
booking_data = {
    "teacher_id": "teacher-uuid",
    "start_time": "2025-01-15T09:00:00Z",
    "duration": 60
}
response = requests.post(
    "http://localhost:8000/api/bookings/bookings/",
    json=booking_data,
    headers={"Authorization": "Bearer student-token"}
)

# 3. Teacher confirms booking
booking_id = response.json()["id"]
response = requests.post(
    f"http://localhost:8000/api/bookings/bookings/{booking_id}/confirm/",
    headers={"Authorization": "Bearer teacher-token"}
)
```

## Migration Required

To use this enhanced system, you need to run:

```bash
python manage.py makemigrations bookings
python manage.py migrate
```

The existing models already have the necessary Zoom fields, so no schema changes are required.

## Switching to Enhanced System

Update your main `urls.py` to use the enhanced booking URLs:

```python
# In rag_app/urls.py, change:
path('api/bookings/', include('bookings.urls')),

# To:
path('api/bookings/', include('bookings.urls_enhanced')),
```
