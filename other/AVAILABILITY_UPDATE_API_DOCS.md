# Teacher Availability Update API Documentation

## Overview
This document covers all the update operations available for teacher availability slots, including individual updates, bulk updates, schedule replacement, and deletion operations.

## Available Update Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/api/bookings/availability/{id}/` | Update individual availability slot |
| PUT | `/api/bookings/availability/{id}/` | Replace individual availability slot |
| DELETE | `/api/bookings/availability/{id}/` | Delete individual availability slot |
| PUT/PATCH | `/api/bookings/availability/bulk/update/` | Update multiple slots at once |
| DELETE | `/api/bookings/availability/bulk/delete/` | Delete multiple slots at once |
| PUT | `/api/bookings/availability/replace/` | Replace entire weekly schedule |
| GET | `/api/bookings/availability/weekly/` | Get teacher's complete weekly availability |

## Authentication
All endpoints require teacher authentication using Bearer token:
```
Authorization: Bearer <teacher_access_token>
```

## Individual Slot Operations

### Update Single Availability Slot
**PATCH/PUT** `/api/bookings/availability/{id}/`

Updates an individual availability slot. Teachers can only update their own slots.

**Request Body (PATCH - partial update):**
```json
{
    "start_time": "08:00:00",
    "end_time": "18:00:00"
}
```

**Request Body (PUT - full replacement):**
```json
{
    "day_of_week": 0,
    "start_time": "08:00:00",
    "end_time": "18:00:00",
    "is_recurring": true
}
```

**Response (200 OK):**
```json
{
    "id": 42,
    "day_of_week": 0,
    "start_time": "08:00:00",
    "end_time": "18:00:00",
    "is_recurring": true,
    "date": null,
    "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
}
```

### Delete Single Availability Slot
**DELETE** `/api/bookings/availability/{id}/`

Deletes an individual availability slot. Teachers can only delete their own slots.

**Response (204 No Content):**
```
(Empty response body)
```

## Bulk Operations

### Bulk Update Multiple Slots
**PUT/PATCH** `/api/bookings/availability/bulk/update/`

Updates multiple availability slots in a single request. Each slot must include its ID.

**Request Body:**
```json
[
    {
        "id": 42,
        "start_time": "08:00:00",
        "end_time": "18:00:00"
    },
    {
        "id": 43,
        "day_of_week": 1,
        "start_time": "10:00:00",
        "end_time": "16:00:00",
        "is_recurring": true
    }
]
```

**Alternative Wrapped Format:**
```json
{
    "availabilities": [
        {
            "id": 42,
            "start_time": "08:00:00",
            "end_time": "18:00:00"
        },
        {
            "id": 43,
            "start_time": "10:00:00",
            "end_time": "16:00:00"
        }
    ]
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully updated 2 availability slots",
    "availabilities": [
        {
            "id": 42,
            "day_of_week": 0,
            "start_time": "08:00:00",
            "end_time": "18:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        },
        {
            "id": 43,
            "day_of_week": 1,
            "start_time": "10:00:00",
            "end_time": "16:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        }
    ]
}
```

### Bulk Delete Multiple Slots
**DELETE** `/api/bookings/availability/bulk/delete/`

Deletes multiple availability slots in a single request.

**Request Body (Array of IDs):**
```json
[42, 43, 44]
```

**Request Body (Array of Objects):**
```json
[
    {"id": 42},
    {"id": 43},
    {"id": 44}
]
```

**Request Body (Wrapped Format):**
```json
{
    "ids": [42, 43, 44]
}
```

**Response (200 OK):**
```json
{
    "message": "Successfully deleted 3 availability slots",
    "deleted_ids": [42, 43, 44]
}
```

### Replace Entire Weekly Schedule
**PUT** `/api/bookings/availability/replace/`

Replaces the teacher's entire weekly recurring schedule. This will delete all existing recurring availability slots and create new ones.

**Request Body:**
```json
[
    {
        "day_of_week": 0,
        "start_time": "08:00:00",
        "end_time": "12:00:00",
        "is_recurring": true
    },
    {
        "day_of_week": 2,
        "start_time": "14:00:00",
        "end_time": "18:00:00",
        "is_recurring": true
    },
    {
        "day_of_week": 4,
        "start_time": "10:00:00",
        "end_time": "16:00:00",
        "is_recurring": true
    }
]
```

**Response (200 OK):**
```json
{
    "message": "Successfully replaced weekly schedule with 3 availability slots",
    "availabilities": [
        {
            "id": 45,
            "day_of_week": 0,
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        },
        {
            "id": 46,
            "day_of_week": 2,
            "start_time": "14:00:00",
            "end_time": "18:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        },
        {
            "id": 47,
            "day_of_week": 4,
            "start_time": "10:00:00",
            "end_time": "16:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        }
    ]
}
```

## Common Update Scenarios

### 1. Extend Working Hours
**Use Case:** Teacher wants to start earlier and end later on specific days.

```javascript
// Update Monday to extend hours
await fetch('/api/bookings/availability/42/', {
    method: 'PATCH',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        start_time: "07:00:00",  // Start 2 hours earlier
        end_time: "19:00:00"     // End 2 hours later
    })
});
```

### 2. Change Mid-Week Schedule
**Use Case:** Teacher wants different hours for Tuesday, Wednesday, Thursday.

```javascript
// Bulk update multiple days
const updates = [
    {id: 43, start_time: "10:00:00", end_time: "14:00:00"}, // Tuesday
    {id: 44, start_time: "10:00:00", end_time: "14:00:00"}, // Wednesday  
    {id: 45, start_time: "10:00:00", end_time: "14:00:00"}  // Thursday
];

await fetch('/api/bookings/availability/bulk/update/', {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
});
```

### 3. Switch to Weekend-Only Teaching
**Use Case:** Teacher wants to work only weekends.

```javascript
// Replace entire schedule with weekend-only
const weekendSchedule = [
    {day_of_week: 5, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true}, // Saturday
    {day_of_week: 6, start_time: "10:00:00", end_time: "16:00:00", is_recurring: true}  // Sunday
];

await fetch('/api/bookings/availability/replace/', {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(weekendSchedule)
});
```

### 4. Remove Specific Days
**Use Case:** Teacher no longer available on certain days.

```javascript
// Delete Friday and Saturday availability
const slotsToDelete = [47, 48]; // IDs of Friday and Saturday slots

await fetch('/api/bookings/availability/bulk/delete/', {
    method: 'DELETE',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(slotsToDelete)
});
```

### 5. Vacation Mode
**Use Case:** Temporarily remove all availability.

```javascript
// Replace with empty schedule (vacation mode)
await fetch('/api/bookings/availability/replace/', {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify([]) // Empty array removes all recurring availability
});
```

### 6. Add Split Shifts
**Use Case:** Teacher wants morning and evening availability on the same day.

```javascript
// Create multiple slots for the same day (requires individual creation)
const morningSlot = {
    day_of_week: 0, // Monday
    start_time: "08:00:00",
    end_time: "12:00:00",
    is_recurring: true
};

const eveningSlot = {
    day_of_week: 0, // Monday
    start_time: "18:00:00", 
    end_time: "21:00:00",
    is_recurring: true
};

// Create both slots
await fetch('/api/bookings/availability/bulk/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${teacherToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify([morningSlot, eveningSlot])
});
```

## Error Responses

### Validation Errors (400 Bad Request)
```json
{
    "error": "Failed to update some availability slots",
    "details": [
        {
            "index": 0,
            "id": 42,
            "errors": {
                "start_time": ["Start time must be before end time"]
            }
        }
    ]
}
```

### Not Found (404 Not Found)
```json
{
    "detail": "Not found."
}
```

### Permission Denied (403 Forbidden)
```json
{
    "error": "Only teachers can update availability slots"
}
```

### Missing Slot IDs (400 Bad Request)
```json
{
    "error": "Some availability slots not found or not owned by teacher",
    "missing_ids": [99999, 99998]
}
```

## Frontend Integration Examples

### React Component for Schedule Management

```jsx
import React, { useState, useEffect } from 'react';

const AvailabilityManager = () => {
    const [availabilities, setAvailabilities] = useState([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    // Load current availabilities
    const loadAvailabilities = async () => {
        try {
            const response = await fetch('/api/bookings/availability/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`
                }
            });
            const data = await response.json();
            setAvailabilities(data);
        } catch (error) {
            setMessage(`Error loading availabilities: ${error.message}`);
        }
    };

    // Update single availability
    const updateAvailability = async (id, updateData) => {
        setLoading(true);
        try {
            const response = await fetch(`/api/bookings/availability/${id}/`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            });

            if (response.ok) {
                setMessage('✅ Availability updated successfully!');
                loadAvailabilities();
            } else {
                const error = await response.json();
                setMessage(`❌ Update failed: ${error.detail || error.error}`);
            }
        } catch (error) {
            setMessage(`❌ Network error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Bulk update multiple availabilities
    const bulkUpdate = async (updates) => {
        setLoading(true);
        try {
            const response = await fetch('/api/bookings/availability/bulk/update/', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (response.ok) {
                const result = await response.json();
                setMessage(`✅ ${result.message}`);
                loadAvailabilities();
            } else {
                const error = await response.json();
                setMessage(`❌ Bulk update failed: ${error.error}`);
            }
        } catch (error) {
            setMessage(`❌ Network error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Delete availabilities
    const deleteAvailabilities = async (ids) => {
        setLoading(true);
        try {
            const response = await fetch('/api/bookings/availability/bulk/delete/', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(ids)
            });

            if (response.ok) {
                const result = await response.json();
                setMessage(`✅ ${result.message}`);
                loadAvailabilities();
            } else {
                const error = await response.json();
                setMessage(`❌ Delete failed: ${error.error}`);
            }
        } catch (error) {
            setMessage(`❌ Network error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // Replace entire schedule
    const replaceSchedule = async (newSchedule) => {
        setLoading(true);
        try {
            const response = await fetch('/api/bookings/availability/replace/', {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newSchedule)
            });

            if (response.ok) {
                const result = await response.json();
                setMessage(`✅ ${result.message}`);
                loadAvailabilities();
            } else {
                const error = await response.json();
                setMessage(`❌ Schedule replacement failed: ${error.error}`);
            }
        } catch (error) {
            setMessage(`❌ Network error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadAvailabilities();
    }, []);

    const handleTimeChange = (id, field, value) => {
        const updateData = { [field]: value + ':00' };
        updateAvailability(id, updateData);
    };

    const handleDeleteDay = (dayOfWeek) => {
        const slotsToDelete = availabilities
            .filter(slot => slot.day_of_week === dayOfWeek)
            .map(slot => slot.id);
        
        if (slotsToDelete.length > 0) {
            deleteAvailabilities(slotsToDelete);
        }
    };

    const groupedAvailabilities = dayNames.map((dayName, dayIndex) => ({
        day: dayName,
        dayIndex,
        slots: availabilities.filter(slot => slot.day_of_week === dayIndex)
    }));

    return (
        <div className="availability-manager">
            <h2>Manage Your Availability</h2>
            
            {message && <div className="message">{message}</div>}
            
            <div className="quick-actions">
                <button 
                    onClick={() => replaceSchedule([])} 
                    disabled={loading}
                    className="vacation-mode"
                >
                    🏖️ Vacation Mode (Remove All)
                </button>
                
                <button 
                    onClick={() => {
                        const weekdaySchedule = Array.from({length: 5}, (_, i) => ({
                            day_of_week: i,
                            start_time: "09:00:00",
                            end_time: "17:00:00",
                            is_recurring: true
                        }));
                        replaceSchedule(weekdaySchedule);
                    }}
                    disabled={loading}
                    className="preset-schedule"
                >
                    📅 Set Weekday 9-5 Schedule
                </button>
            </div>

            <div className="schedule-grid">
                {groupedAvailabilities.map(({ day, dayIndex, slots }) => (
                    <div key={dayIndex} className="day-section">
                        <h3>
                            {day}
                            {slots.length > 0 && (
                                <button 
                                    onClick={() => handleDeleteDay(dayIndex)}
                                    className="delete-day"
                                    disabled={loading}
                                >
                                    ❌ Remove Day
                                </button>
                            )}
                        </h3>
                        
                        {slots.length === 0 ? (
                            <p>No availability</p>
                        ) : (
                            slots.map(slot => (
                                <div key={slot.id} className="time-slot">
                                    <input
                                        type="time"
                                        value={slot.start_time.slice(0, 5)}
                                        onChange={(e) => handleTimeChange(slot.id, 'start_time', e.target.value)}
                                        disabled={loading}
                                    />
                                    <span> to </span>
                                    <input
                                        type="time"
                                        value={slot.end_time.slice(0, 5)}
                                        onChange={(e) => handleTimeChange(slot.id, 'end_time', e.target.value)}
                                        disabled={loading}
                                    />
                                    <button 
                                        onClick={() => deleteAvailabilities([slot.id])}
                                        disabled={loading}
                                        className="delete-slot"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                ))}
            </div>
            
            {loading && <div className="loading">Processing...</div>}
        </div>
    );
};

export default AvailabilityManager;
```

### Python Client Example

```python
import requests

class AvailabilityManager:
    def __init__(self, base_url, teacher_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {teacher_token}',
            'Content-Type': 'application/json'
        }
    
    def update_slot(self, slot_id, update_data):
        """Update a single availability slot"""
        response = requests.patch(
            f'{self.base_url}/api/bookings/availability/{slot_id}/',
            json=update_data,
            headers=self.headers
        )
        return response.json()
    
    def bulk_update(self, updates):
        """Update multiple slots at once"""
        response = requests.put(
            f'{self.base_url}/api/bookings/availability/bulk/update/',
            json=updates,
            headers=self.headers
        )
        return response.json()
    
    def delete_slots(self, slot_ids):
        """Delete multiple slots"""
        response = requests.delete(
            f'{self.base_url}/api/bookings/availability/bulk/delete/',
            json=slot_ids,
            headers=self.headers
        )
        return response.json()
    
    def replace_schedule(self, new_schedule):
        """Replace entire weekly schedule"""
        response = requests.put(
            f'{self.base_url}/api/bookings/availability/replace/',
            json=new_schedule,
            headers=self.headers
        )
        return response.json()

# Usage examples
manager = AvailabilityManager('http://localhost:8000', teacher_token)

# Extend Monday hours
manager.update_slot(42, {
    'start_time': '08:00:00',
    'end_time': '18:00:00'
})

# Update multiple days to shorter hours
manager.bulk_update([
    {'id': 43, 'start_time': '10:00:00', 'end_time': '14:00:00'},
    {'id': 44, 'start_time': '10:00:00', 'end_time': '14:00:00'}
])

# Switch to weekend-only teaching
manager.replace_schedule([
    {'day_of_week': 5, 'start_time': '09:00:00', 'end_time': '17:00:00', 'is_recurring': True},
    {'day_of_week': 6, 'start_time': '10:00:00', 'end_time': '16:00:00', 'is_recurring': True}
])
```

## Getting Teacher's Weekly Availability

### Weekly Availability Endpoint
**GET** `/api/bookings/availability/weekly/`

Retrieves a teacher's complete weekly availability schedule in a structured format. This endpoint is accessible by both students and teachers, making it perfect for schedule browsing and lesson booking.

**Parameters:**
- `teacher_id` (required): The UUID of the teacher

**Authentication:**
- Accessible by both students and teachers
- Requires valid access token

**Example Request:**
```bash
curl -X GET \
  "http://localhost:8000/api/bookings/availability/weekly/?teacher_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer your_access_token_here"
```

**Response (200 OK):**
```json
{
    "teacher": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Smith",
        "email": "john.smith@example.com",
        "hourly_rate": "25.00",
        "experience_years": 5,
        "bio": "Experienced English teacher specializing in business communication"
    },
    "weekly_schedule": {
        "Monday": {
            "available": true,
            "slots": [
                {
                    "id": "availability-uuid-1",
                    "start_time": "09:00:00",
                    "end_time": "12:00:00",
                    "duration_hours": 3.0,
                    "is_recurring": true
                },
                {
                    "id": "availability-uuid-2",
                    "start_time": "14:00:00",
                    "end_time": "18:00:00",
                    "duration_hours": 4.0,
                    "is_recurring": true
                }
            ]
        },
        "Tuesday": {
            "available": true,
            "slots": [
                {
                    "id": "availability-uuid-3",
                    "start_time": "10:00:00",
                    "end_time": "16:00:00",
                    "duration_hours": 6.0,
                    "is_recurring": true
                }
            ]
        },
        "Wednesday": {
            "available": false,
            "slots": []
        },
        "Thursday": {
            "available": false,
            "slots": []
        },
        "Friday": {
            "available": true,
            "slots": [
                {
                    "id": "availability-uuid-4",
                    "start_time": "13:00:00",
                    "end_time": "19:00:00",
                    "duration_hours": 6.0,
                    "is_recurring": true
                }
            ]
        },
        "Saturday": {
            "available": true,
            "slots": [
                {
                    "id": "availability-uuid-5",
                    "start_time": "08:00:00",
                    "end_time": "14:00:00",
                    "duration_hours": 6.0,
                    "is_recurring": true
                }
            ]
        },
        "Sunday": {
            "available": false,
            "slots": []
        }
    },
    "summary": {
        "total_availability_slots": 5,
        "available_days_count": 4,
        "total_weekly_hours": 25.0,
        "days_with_availability": ["Monday", "Tuesday", "Friday", "Saturday"]
    }
}
```

**Error Responses:**

**400 Bad Request - Missing teacher_id:**
```json
{
    "error": "teacher_id parameter is required"
}
```

**404 Not Found - Teacher doesn't exist:**
```json
{
    "error": "Teacher not found"
}
```

**Use Cases:**

1. **For Students:** Browse teacher schedules to find available time slots for booking lessons
2. **For Teachers:** View their own weekly schedule overview
3. **For Admin:** Monitor teacher availability across the platform
4. **For Frontend:** Display weekly calendar views with teacher availability

**Frontend Integration Examples:**

**JavaScript/React:**
```javascript
const getTeacherWeeklySchedule = async (teacherId) => {
    const response = await fetch(`/api/bookings/availability/weekly/?teacher_id=${teacherId}`, {
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    });
    
    if (response.ok) {
        const data = await response.json();
        return data;
    }
    throw new Error('Failed to fetch teacher schedule');
};

// Usage in component
useEffect(() => {
    getTeacherWeeklySchedule(teacherId)
        .then(data => {
            setTeacherInfo(data.teacher);
            setWeeklySchedule(data.weekly_schedule);
            setSummary(data.summary);
        })
        .catch(error => console.error(error));
}, [teacherId]);
```

**Python Client:**
```python
def get_teacher_weekly_availability(teacher_id, access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        f'/api/bookings/availability/weekly/?teacher_id={teacher_id}',
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

# Display formatted schedule
data = get_teacher_weekly_availability('teacher-id', 'token')
print(f"Teacher: {data['teacher']['name']}")
print(f"Available {data['summary']['available_days_count']} days per week")
print(f"Total {data['summary']['total_weekly_hours']} hours")

for day, schedule in data['weekly_schedule'].items():
    if schedule['available']:
        slots = [f"{slot['start_time'][:5]}-{slot['end_time'][:5]}" 
                for slot in schedule['slots']]
        print(f"{day}: {', '.join(slots)}")
```

## Security & Permissions

1. **Teacher-Only Access**: Only users with TEACHER role can update availability
2. **Own Slots Only**: Teachers can only update/delete their own availability slots
3. **Universal Read Access**: Both students and teachers can view teacher schedules
4. **Validation**: All time and day validations are enforced
5. **Transaction Safety**: Bulk operations are atomic (all succeed or all fail)

## Performance Notes

1. **Bulk Operations**: Use bulk endpoints for multiple changes to reduce API calls
2. **Partial Updates**: Use PATCH for partial updates to minimize data transfer
3. **Atomic Transactions**: Database transactions ensure data consistency
4. **Efficient Queries**: Optimized database queries for bulk operations
5. **Weekly View Caching**: Consider caching weekly availability data for frequently accessed teachers

This comprehensive update system provides teachers with full control over their availability schedules while maintaining data integrity and security. The weekly availability endpoint enables seamless schedule browsing for students and comprehensive schedule management for teachers.
