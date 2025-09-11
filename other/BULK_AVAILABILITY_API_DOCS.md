# Bulk Teacher Availability API Documentation

## Overview
The Bulk Teacher Availability API allows teachers to set their availability for multiple days of the week in a single request, instead of creating individual availability slots one by one.

## Endpoint
```
POST /api/bookings/availability/bulk/
```

## Authentication
Requires teacher authentication using Bearer token:
```
Authorization: Bearer <teacher_access_token>
```

## Request Formats

### Format 1: Direct Array (Recommended)
```json
[
    {
        "day_of_week": 0,
        "start_time": "09:00:00",
        "end_time": "18:00:00", 
        "is_recurring": true
    },
    {
        "day_of_week": 1,
        "start_time": "09:00:00",
        "end_time": "18:00:00", 
        "is_recurring": true
    }
]
```

### Format 2: Wrapped Format
```json
{
    "availabilities": [
        {
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00", 
            "is_recurring": true
        },
        {
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "18:00:00", 
            "is_recurring": true
        }
    ]
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `day_of_week` | Integer | Yes | Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday) |
| `start_time` | Time | Yes | Start time in HH:MM:SS format |
| `end_time` | Time | Yes | End time in HH:MM:SS format |
| `is_recurring` | Boolean | No | Whether this availability repeats weekly (default: true) |
| `date` | Date | No | Specific date for non-recurring availability (YYYY-MM-DD) |

## Day of Week Values
- `0` = Monday
- `1` = Tuesday  
- `2` = Wednesday
- `3` = Thursday
- `4` = Friday
- `5` = Saturday
- `6` = Sunday

## Response Format

### Success Response (201 Created)
```json
{
    "message": "Successfully created/updated 5 availability slots",
    "availabilities": [
        {
            "id": 1,
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        },
        {
            "id": 2,
            "day_of_week": 1,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "is_recurring": true,
            "date": null,
            "teacher": "30139770-0d26-4e9e-8b36-8efb33ed7b2e"
        }
    ]
}
```

## Common Use Cases

### 1. Full-Time Teacher (Monday-Friday, 9 AM - 5 PM)
```json
[
    {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 3, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 4, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true}
]
```

### 2. Part-Time Teacher (Tuesday/Thursday Evenings)
```json
[
    {"day_of_week": 1, "start_time": "18:00:00", "end_time": "21:00:00", "is_recurring": true},
    {"day_of_week": 3, "start_time": "18:00:00", "end_time": "21:00:00", "is_recurring": true}
]
```

### 3. Weekend Teacher
```json
[
    {"day_of_week": 5, "start_time": "08:00:00", "end_time": "12:00:00", "is_recurring": true},
    {"day_of_week": 6, "start_time": "09:00:00", "end_time": "13:00:00", "is_recurring": true}
]
```

### 4. Flexible Schedule (Different Hours Each Day)
```json
[
    {"day_of_week": 0, "start_time": "08:00:00", "end_time": "12:00:00", "is_recurring": true},
    {"day_of_week": 1, "start_time": "14:00:00", "end_time": "18:00:00", "is_recurring": true},
    {"day_of_week": 2, "start_time": "10:00:00", "end_time": "16:00:00", "is_recurring": true},
    {"day_of_week": 3, "start_time": "09:00:00", "end_time": "13:00:00", "is_recurring": true},
    {"day_of_week": 4, "start_time": "15:00:00", "end_time": "19:00:00", "is_recurring": true}
]
```

## Behavior

### Creating New Availability
- If no existing availability exists for the teacher/day/time combination, a new slot is created
- Multiple slots can be created for the same day with different time ranges

### Updating Existing Availability
- If an exact match exists (same teacher, day_of_week, start_time, end_time, is_recurring), the existing record is updated
- This allows teachers to modify their existing availability

### Validation Rules
1. `start_time` must be before `end_time`
2. `day_of_week` must be between 0-6
3. Time format must be HH:MM:SS
4. Only users with TEACHER role can create availability
5. At least one availability slot is required

## Error Responses

### Validation Errors (400 Bad Request)
```json
{
    "error": "Validation failed for some availability slots",
    "details": [
        {
            "index": 0,
            "data": {"day_of_week": 0, "start_time": "18:00:00", "end_time": "09:00:00"},
            "errors": {
                "non_field_errors": ["Start time must be before end time"]
            }
        }
    ]
}
```

### Permission Denied (403 Forbidden)
```json
{
    "error": "Only teachers can create availability slots"
}
```

### Empty Data (400 Bad Request)
```json
{
    "error": "At least one availability slot is required"
}
```

### Invalid Format (400 Bad Request)
```json
{
    "error": "Invalid data format. Expected array of availability objects or {'availabilities': [...]}"
}
```

## Frontend Integration Examples

### JavaScript/Fetch API
```javascript
const createWeeklyAvailability = async (scheduleData) => {
    try {
        const response = await fetch('/api/bookings/availability/bulk/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${teacherToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scheduleData)
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Success:', result.message);
            return result.availabilities;
        } else {
            const error = await response.json();
            console.error('Error:', error);
            throw new Error(error.error);
        }
    } catch (error) {
        console.error('Network error:', error);
        throw error;
    }
};

// Usage
const weekdaySchedule = [
    {day_of_week: 0, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 1, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 2, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 3, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
    {day_of_week: 4, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true}
];

createWeeklyAvailability(weekdaySchedule)
    .then(availabilities => {
        console.log('Created availabilities:', availabilities);
    })
    .catch(error => {
        console.error('Failed to create availability:', error);
    });
```

### React Component Example
```jsx
import React, { useState } from 'react';

const WeeklyAvailabilityForm = () => {
    const [schedule, setSchedule] = useState([
        {day_of_week: 0, start_time: "09:00", end_time: "17:00", is_recurring: true},
        {day_of_week: 1, start_time: "09:00", end_time: "17:00", is_recurring: true},
        {day_of_week: 2, start_time: "09:00", end_time: "17:00", is_recurring: true},
        {day_of_week: 3, start_time: "09:00", end_time: "17:00", is_recurring: true},
        {day_of_week: 4, start_time: "09:00", end_time: "17:00", is_recurring: true}
    ]);
    
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    const handleTimeChange = (dayIndex, field, value) => {
        const newSchedule = [...schedule];
        newSchedule[dayIndex][field] = value + ':00'; // Add seconds
        setSchedule(newSchedule);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        try {
            const response = await fetch('/api/bookings/availability/bulk/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('teacherToken')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(schedule)
            });

            const result = await response.json();
            
            if (response.ok) {
                setMessage(`✅ ${result.message}`);
            } else {
                setMessage(`❌ ${result.error}`);
            }
        } catch (error) {
            setMessage(`❌ Network error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <h2>Set Weekly Availability</h2>
            
            {schedule.map((day, index) => (
                <div key={day.day_of_week} style={{marginBottom: '15px'}}>
                    <label>{dayNames[day.day_of_week]}:</label>
                    <input
                        type="time"
                        value={day.start_time.slice(0, 5)}
                        onChange={(e) => handleTimeChange(index, 'start_time', e.target.value)}
                    />
                    <span> to </span>
                    <input
                        type="time"
                        value={day.end_time.slice(0, 5)}
                        onChange={(e) => handleTimeChange(index, 'end_time', e.target.value)}
                    />
                </div>
            ))}
            
            <button type="submit" disabled={loading}>
                {loading ? 'Saving...' : 'Save Weekly Availability'}
            </button>
            
            {message && <p>{message}</p>}
        </form>
    );
};

export default WeeklyAvailabilityForm;
```

### Python/requests Example
```python
import requests

def set_teacher_weekly_availability(teacher_token, weekly_schedule):
    """
    Set teacher availability for multiple days
    
    Args:
        teacher_token: JWT token for teacher authentication
        weekly_schedule: List of availability objects
    
    Returns:
        API response data
    """
    headers = {
        'Authorization': f'Bearer {teacher_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'http://localhost:8000/api/bookings/availability/bulk/',
        json=weekly_schedule,
        headers=headers
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        response.raise_for_status()

# Example usage
weekly_schedule = [
    {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
    {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
    {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
    {"day_of_week": 3, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True},
    {"day_of_week": 4, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": True}
]

try:
    result = set_teacher_weekly_availability(teacher_token, weekly_schedule)
    print(f"Success: {result['message']}")
    print(f"Created {len(result['availabilities'])} availability slots")
except requests.HTTPError as e:
    print(f"Error: {e.response.json()}")
```

## Testing with cURL

### Create Full Week Availability
```bash
curl -X POST http://localhost:8000/api/bookings/availability/bulk/ \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 3, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true},
    {"day_of_week": 4, "start_time": "09:00:00", "end_time": "17:00:00", "is_recurring": true}
  ]'
```

### Create Weekend Only Availability
```bash
curl -X POST http://localhost:8000/api/bookings/availability/bulk/ \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"day_of_week": 5, "start_time": "10:00:00", "end_time": "14:00:00", "is_recurring": true},
    {"day_of_week": 6, "start_time": "12:00:00", "end_time": "16:00:00", "is_recurring": true}
  ]'
```

## Comparison with Individual Creation

### Before (Individual Creation)
```javascript
// Had to make 5 separate API calls
for (let day = 0; day < 5; day++) {
    await fetch('/api/bookings/availability/', {
        method: 'POST',
        headers: {...},
        body: JSON.stringify({
            day_of_week: day,
            start_time: "09:00:00",
            end_time: "17:00:00",
            is_recurring: true
        })
    });
}
```

### After (Bulk Creation)
```javascript
// Single API call for the entire week
await fetch('/api/bookings/availability/bulk/', {
    method: 'POST',
    headers: {...},
    body: JSON.stringify([
        {day_of_week: 0, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
        {day_of_week: 1, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
        {day_of_week: 2, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
        {day_of_week: 3, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true},
        {day_of_week: 4, start_time: "09:00:00", end_time: "17:00:00", is_recurring: true}
    ])
});
```

## Benefits

1. **Reduced API Calls**: Set entire week availability in one request
2. **Atomic Operations**: All availability slots are created/updated together or none at all
3. **Better Performance**: Fewer database queries and network requests
4. **Improved UX**: Faster form submissions for teachers
5. **Consistent Data**: Transaction ensures data integrity
6. **Flexible**: Supports both array and wrapped request formats

This bulk creation endpoint significantly improves the user experience for teachers setting up their weekly availability schedules.
