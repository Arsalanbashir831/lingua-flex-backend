# 📋 Reschedule Booking Endpoints - Postman Testing Guide

## 🔗 Base URL
```
{{base_url}} = http://127.0.0.1:8000/api/bookings
```

---

## 📌 Current Available Endpoint

### 1. **Reschedule Booking** (Direct Reschedule)
**URL:** `POST {{base_url}}/bookings/{{booking_id}}/reschedule/`

**Description:** Directly reschedules a booking to a new time slot

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{your_jwt_token}}
```

**Request Body:**
```json
{
    "new_start_time": "2025-09-20T10:00:00Z",
    "new_end_time": "2025-09-20T11:00:00Z",
    "reason": "Need to reschedule due to conflict"
}
```

**Alternative Request Body (using duration):**
```json
{
    "start_time": "2025-09-20T10:00:00Z",
    "duration": 60,
    "reason": "Need to reschedule due to conflict"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Booking rescheduled successfully",
    "changes": {
        "old_start_time": "2025-09-18T09:00:00Z",
        "old_end_time": "2025-09-18T10:00:00Z",
        "new_start_time": "2025-09-20T10:00:00Z",
        "new_end_time": "2025-09-20T11:00:00Z",
        "reason": "Need to reschedule due to conflict"
    },
    "booking": {
        "id": "booking-uuid-here",
        "status": "CONFIRMED",
        "reschedule_request_status": "NONE",
        "reschedule_requested_by": null,
        // ... other booking fields
    }
}
```

**Error Responses:**
```json
// 400 - Bad Request
{
    "error": "new_start_time or start_time is required"
}

// 403 - Forbidden
{
    "error": "You can only reschedule your own bookings"
}

// 400 - Invalid Status
{
    "error": "Cannot reschedule completed or cancelled sessions"
}

// 400 - Time Conflict
{
    "error": "New time slot is not available"
}
```

---

## 🆕 New Enhanced Reschedule Workflow Endpoints

### 2. **Request Reschedule** (✅ Now Implemented)
**URL:** `POST {{base_url}}/bookings/{{booking_id}}/request-reschedule/`

**Description:** Request a reschedule that requires confirmation from the other party

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{your_jwt_token}}
```

**Request Body:**
```json
{
    "new_start_time": "2025-09-20T10:00:00Z",
    "new_end_time": "2025-09-20T11:00:00Z",
    "reason": "Emergency meeting came up"
}
```

**Alternative Request Body (using duration):**
```json
{
    "start_time": "2025-09-20T10:00:00Z",
    "duration": 60,
    "reason": "Emergency meeting came up"
}
```

**Expected Response (200 OK):**
```json
{
    "message": "Reschedule request sent successfully",
    "reschedule_request": {
        "requested_by": "STUDENT",
        "status": "PENDING",
        "requested_start_time": "2025-09-20T10:00:00Z",
        "requested_end_time": "2025-09-20T11:00:00Z",
        "reason": "Emergency meeting came up",
        "awaiting_response_from": "teacher@example.com"
    },
    "booking": {
        "id": "booking-uuid-here",
        "reschedule_request_status": "PENDING",
        "reschedule_requested_by": "STUDENT",
        // ... other booking fields
    }
}
```

**Error Responses:**
```json
// 400 - Already pending
{
    "error": "There is already a pending reschedule request for this booking"
}

// 400 - Time not available
{
    "error": "Requested time slot is not available"
}

// 403 - Not authorized
{
    "error": "You can only request reschedule for your own bookings"
}
```

### 3. **Respond to Reschedule Request** (✅ Now Implemented)
**URL:** `POST {{base_url}}/bookings/{{booking_id}}/respond-reschedule/`

**Description:** Confirm or decline a pending reschedule request

**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{your_jwt_token}}
```

**Request Body (Confirm):**
```json
{
    "action": "CONFIRMED",
    "response_message": "Confirmed, that time works for me"
}
```

**Request Body (Decline):**
```json
{
    "action": "DECLINED", 
    "response_message": "Sorry, I'm not available at that time"
}
```

**Expected Response (Confirmed - 200 OK):**
```json
{
    "message": "Reschedule request confirmed and booking updated successfully",
    "changes": {
        "old_start_time": "2025-09-18T09:00:00Z",
        "old_end_time": "2025-09-18T10:00:00Z",
        "new_start_time": "2025-09-20T10:00:00Z",
        "new_end_time": "2025-09-20T11:00:00Z",
        "response_message": "Confirmed, that time works for me"
    },
    "booking": {
        "id": "booking-uuid-here",
        "reschedule_request_status": "NONE",
        "reschedule_requested_by": null,
        "start_time": "2025-09-20T10:00:00Z",
        "end_time": "2025-09-20T11:00:00Z"
    }
}
```

**Expected Response (Declined - 200 OK):**
```json
{
    "message": "Reschedule request declined",
    "response_message": "Sorry, I'm not available at that time",
    "booking": {
        "id": "booking-uuid-here", 
        "reschedule_request_status": "NONE",
        "reschedule_requested_by": null,
        // ... original booking times remain unchanged
    }
}
```

**Error Responses:**
```json
// 400 - Missing action
{
    "error": "action is required ('CONFIRMED' or 'DECLINED')"
}

// 403 - Wrong user responding
{
    "error": "Only the teacher can respond to this reschedule request"
}

// 400 - No pending request
{
    "error": "No pending reschedule request found for this booking"
}
```

---

## 🔮 Suggested Enhanced Reschedule Workflow

**Note:** Based on your new reschedule tracking fields, here's how the workflow should ideally work. You may need to implement these endpoints:

---

## 📝 Postman Collection Setup

### Environment Variables
Create a Postman environment with these variables:

```
base_url: http://127.0.0.1:8000/api/bookings
jwt_token: your_actual_jwt_token_here
booking_id: uuid-of-booking-to-test
```

### Pre-request Scripts
Add this script to automatically get a fresh JWT token:

```javascript
// Pre-request script for authentication
pm.sendRequest({
    url: pm.environment.get("base_url").replace("/api/bookings", "") + "/auth/login/",
    method: 'POST',
    header: {
        'Content-Type': 'application/json'
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            email: "your_email@example.com",
            password: "your_password"
        })
    }
}, function (err, response) {
    if (response.json().access) {
        pm.environment.set("jwt_token", response.json().access);
    }
});
```

---

## 🧪 Test Scenarios

### Scenario 1: Successful Direct Reschedule
1. **Create a booking** first (use booking creation endpoint)
2. **Get booking ID** from the response
3. **Call reschedule endpoint** with valid new time
4. **Verify response** contains updated times

### Scenario 2: Complete Reschedule Request Workflow
1. **Student requests reschedule** using `/request-reschedule/`
2. **Verify booking status** is "PENDING" with correct requester
3. **Teacher responds with confirmation** using `/respond-reschedule/`
4. **Verify booking times are updated** and status reset to "NONE"

### Scenario 3: Declined Reschedule Request
1. **Teacher requests reschedule** using `/request-reschedule/`
2. **Student declines** using `/respond-reschedule/` with action "DECLINED"
3. **Verify original booking times unchanged** and status reset to "NONE"

### Scenario 4: Unauthorized Access
1. **Use wrong user token** (different student/teacher)
2. **Call reschedule endpoint**
3. **Expect 403 Forbidden error**

### Scenario 5: Invalid Time Slot
1. **Use existing booking time** for another session
2. **Call reschedule endpoint**
3. **Expect time conflict error**

### Scenario 6: Invalid Status
1. **Use completed or cancelled booking**
2. **Call reschedule endpoint**
3. **Expect status error**

### Scenario 7: Duplicate Reschedule Request
1. **Send reschedule request** 
2. **Try to send another request** before first is resolved
3. **Expect "already pending" error**

### Scenario 8: Responding to Non-existent Request
1. **Try to respond to reschedule** when no request is pending
2. **Expect "no pending request" error**

---

## 🔍 Testing Checklist

- [ ] Test direct reschedule with valid student account
- [ ] Test direct reschedule with valid teacher account  
- [ ] Test reschedule request workflow (student requests)
- [ ] Test reschedule request workflow (teacher requests)
- [ ] Test confirm reschedule response
- [ ] Test decline reschedule response
- [ ] Test with unauthorized user
- [ ] Test with invalid booking ID
- [ ] Test with past date/time
- [ ] Test with conflicting time slot
- [ ] Test with completed booking
- [ ] Test with cancelled booking
- [ ] Test duplicate reschedule request
- [ ] Test responding to non-existent request
- [ ] Test wrong user trying to respond
- [ ] Test missing required fields
- [ ] Test invalid datetime format
- [ ] Test invalid action values

---

## 📊 Sample Test Data

### Valid Booking IDs for Testing
```
# Replace these with actual UUIDs from your database
student_booking_id: "123e4567-e89b-12d3-a456-426614174000"
teacher_booking_id: "123e4567-e89b-12d3-a456-426614174001"
```

### Valid Date/Time Examples
```
# Future dates (adjust based on current date)
"2025-09-20T10:00:00Z"  # Morning slot
"2025-09-20T14:30:00Z"  # Afternoon slot
"2025-09-21T09:15:00Z"  # Next day
```

### Test User Tokens
```
# Get these by logging in as different users
student_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
teacher_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
admin_token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## ⚠️ Important Notes

1. **UUID Format**: The current enhanced URLs use UUID format (`<uuid:pk>`)
2. **Timezone**: All datetime values should be in UTC with 'Z' suffix
3. **Authentication**: JWT token required in Authorization header
4. **Permissions**: Only student or teacher involved in the booking can reschedule
5. **Status Check**: Only PENDING or CONFIRMED bookings can be rescheduled

---

## 🚀 Quick Start Commands

```bash
# 1. Start Django server
python manage.py runserver 8000

# 2. Get authentication token
curl -X POST http://127.0.0.1:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","password":"password123"}'

# 3. Test direct reschedule endpoint
curl -X POST http://127.0.0.1:8000/api/bookings/bookings/YOUR_BOOKING_ID/reschedule/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"new_start_time":"2025-09-20T10:00:00Z","new_end_time":"2025-09-20T11:00:00Z","reason":"Testing"}'

# 4. Test request reschedule endpoint
curl -X POST http://127.0.0.1:8000/api/bookings/bookings/YOUR_BOOKING_ID/request-reschedule/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_JWT_TOKEN" \
  -d '{"new_start_time":"2025-09-20T14:00:00Z","duration":60,"reason":"Schedule conflict"}'

# 5. Test respond to reschedule (confirm)
curl -X POST http://127.0.0.1:8000/api/bookings/bookings/YOUR_BOOKING_ID/respond-reschedule/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TEACHER_JWT_TOKEN" \
  -d '{"action":"CONFIRMED","response_message":"Works for me!"}'

# 6. Test respond to reschedule (decline)  
curl -X POST http://127.0.0.1:8000/api/bookings/bookings/YOUR_BOOKING_ID/respond-reschedule/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TEACHER_JWT_TOKEN" \
  -d '{"action":"DECLINED","response_message":"Not available at that time"}'
```

Happy Testing! 🎉

---

## 📋 Reschedule Workflow Summary

### Direct Reschedule (Immediate)
```
Student/Teacher → POST /reschedule/ → Booking Updated Immediately
```

### Request-Response Workflow (Requires Confirmation)
```
1. Student → POST /request-reschedule/ → Booking Status: PENDING
2. Teacher → POST /respond-reschedule/ {"action": "CONFIRMED"} → Booking Updated
   OR
2. Teacher → POST /respond-reschedule/ {"action": "DECLINED"} → Original Times Kept
```

### Status Flow
```
NONE → PENDING → CONFIRMED/DECLINED → NONE
```

### Who Can Do What?
- **Request Reschedule**: Student OR Teacher (booking participant)
- **Respond**: The OTHER participant (not the requester)
- **Direct Reschedule**: Either participant (immediate change)

This gives you maximum flexibility - use direct reschedule for quick changes or request-response workflow when confirmation is needed! 🚀