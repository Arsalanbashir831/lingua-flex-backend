# Enhanced Refund System API Documentation

## Overview
The LinguaFlex refund system provides automatic and manual refund processing based on session completion status:

- **Automatic Refunds**: Sessions that are PENDING, CONFIRMED, or CANCELLED get immediate refunds
- **Manual Review**: Sessions that are COMPLETED require admin approval

---

## 🔄 Student Refund Endpoints

### 1. Request Refund
**Endpoint**: `POST /api/payments/refund/request/`  
**Authentication**: Student Bearer Token Required  
**Description**: Submit a refund request with automatic or manual processing

#### Request Body:
```json
{
  "payment_id": 2,
  "reason": "Student couldn't attend the session",
  "requested_amount_dollars": 13.125
}
```

#### Response - Automatic Refund (Incomplete Session):
```json
{
  "success": true,
  "refund_type": "automatic",
  "message": "Refund processed immediately (session not completed)",
  "refund_request_id": 1,
  "refund_amount": 13.125,
  "stripe_refund_id": "re_1ABC123...",
  "booking_status": "CANCELLED",
  "refund_status": "PROCESSED"
}
```

#### Response - Manual Review (Completed Session):
```json
{
  "success": true,
  "refund_type": "manual_review",
  "message": "Refund request submitted for admin review (session was completed)",
  "refund_request_id": 2,
  "requested_amount": 13.125,
  "status": "PENDING",
  "note": "Completed sessions require manual admin approval"
}
```

#### Error Responses:
```json
{
  "success": false,
  "error": "Refund request already exists for this payment",
  "existing_refund_id": 1,
  "status": "PENDING"
}
```

---

### 2. View Refund History
**Endpoint**: `GET /api/payments/refund/request/`  
**Authentication**: Student Bearer Token Required  
**Description**: Get all refund requests for the authenticated student

#### Response:
```json
{
  "success": true,
  "refund_requests": [
    {
      "id": 1,
      "payment_id": 2,
      "amount_requested": 13.125,
      "amount_refunded": 13.125,
      "status": "PROCESSED",
      "reason": "Student couldn't attend the session",
      "created_at": "2025-09-12T15:30:00Z",
      "refunded_at": "2025-09-12T15:30:05Z",
      "booking_details": {
        "id": 4,
        "status": "CANCELLED",
        "teacher_name": "John Jane",
        "gig_title": "Language Session",
        "session_date": "2025-09-12T12:00:00Z"
      },
      "admin_notes": null
    }
  ]
}
```

---

### 3. Check Refund Status
**Endpoint**: `GET /api/payments/refund/status/{payment_id}/`  
**Authentication**: Student Bearer Token Required  
**Description**: Check refund eligibility and status for a specific payment

#### Response:
```json
{
  "success": true,
  "payment_id": 2,
  "payment_amount": 13.125,
  "payment_status": "COMPLETED",
  "booking_status": "CONFIRMED",
  "can_request_refund": true,
  "refund_requests": [],
  "refund_eligibility": {
    "automatic": true,
    "manual_review": false,
    "reason": "Incomplete sessions get automatic refunds, completed sessions require admin approval"
  }
}
```

---

## 🔧 Admin Refund Management

### 1. View Pending Refunds
**Endpoint**: `GET /api/payments/admin/refund/manage/?status=PENDING`  
**Authentication**: Admin Bearer Token Required  
**Description**: Get all refund requests for admin review

#### Query Parameters:
- `status` (optional): Filter by status (`PENDING`, `APPROVED`, `REJECTED`, `PROCESSED`)

#### Response:
```json
{
  "success": true,
  "refund_requests": [
    {
      "id": 2,
      "student_email": "student@example.com",
      "student_name": "Student Name",
      "teacher_email": "teacher@example.com", 
      "teacher_name": "John Jane",
      "payment_id": 2,
      "original_amount": 13.125,
      "requested_amount": 10.0,
      "reason": "Session quality was poor",
      "booking_status": "COMPLETED",
      "session_date": "2025-09-12T12:00:00Z",
      "gig_title": "Language Session",
      "request_date": "2025-09-12T16:00:00Z",
      "status": "PENDING",
      "admin_notes": null
    }
  ],
  "total": 1
}
```

---

### 2. Approve/Reject Refund
**Endpoint**: `POST /api/payments/admin/refund/manage/`  
**Authentication**: Admin Bearer Token Required  
**Description**: Approve or reject a pending refund request

#### Request Body - Approve:
```json
{
  "refund_request_id": 2,
  "action": "approve",
  "admin_notes": "Approved - valid reason for refund"
}
```

#### Request Body - Reject:
```json
{
  "refund_request_id": 2,
  "action": "reject",
  "admin_notes": "Rejected - session was completed successfully according to teacher feedback"
}
```

#### Response - Approved and Processed:
```json
{
  "success": true,
  "message": "Refund approved and processed",
  "refund_request_id": 2,
  "stripe_refund_id": "re_1ABC123...",
  "amount_refunded": 10.0
}
```

#### Response - Rejected:
```json
{
  "success": true,
  "message": "Refund request rejected",
  "refund_request_id": 2,
  "admin_notes": "Rejected - session was completed successfully according to teacher feedback"
}
```

---

## 📊 Refund Business Logic

### Automatic Refund Conditions:
- Booking status is `PENDING`, `CONFIRMED`, or `CANCELLED`
- Payment status is `COMPLETED`
- No existing refund request for the payment

### Manual Review Conditions:
- Booking status is `COMPLETED`
- Payment status is `COMPLETED`
- No existing refund request for the payment

### Refund Processing:
1. **Student Request**: Student submits refund with reason and amount
2. **Status Check**: System checks if booking is complete or not
3. **Automatic Path**: Immediate Stripe refund for incomplete sessions
4. **Manual Path**: Admin review required for completed sessions
5. **Stripe Integration**: Actual refund processed through Stripe API
6. **Status Updates**: Booking and payment statuses updated accordingly

---

## 🔍 Error Handling

### Common Error Codes:
- `400`: Invalid request data or business rule violation
- `404`: Payment or refund request not found
- `403`: Permission denied (wrong user or not admin)
- `500`: Stripe processing error or internal server error

### Error Response Format:
```json
{
  "success": false,
  "error": "Error message describing the issue",
  "refund_request_id": 123  // If applicable
}
```

---

## 🧪 Testing with Your Payment

Based on your successful payment response:
- **Payment ID**: 2
- **Amount**: $13.125
- **Booking ID**: 4
- **Status**: Payment succeeded

### Test Automatic Refund:
If the booking status is not `COMPLETED`, you can test automatic refund:

```bash
curl -X POST http://localhost:8000/api/payments/refund/request/ \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 2,
    "reason": "Student emergency - cannot attend",
    "requested_amount_dollars": 13.125
  }'
```

### Test Manual Review:
If the booking status is `COMPLETED`, it will go to manual review:

```bash
curl -X POST http://localhost:8000/api/payments/refund/request/ \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 2,
    "reason": "Teacher quality issues",
    "requested_amount_dollars": 10.00
  }'
```

---

## 📝 Notes

1. **Stripe Integration**: Refunds are processed through Stripe and money returns to the original payment method
2. **Platform Fees**: Refund amount includes platform fees if requested
3. **Partial Refunds**: Students can request partial refunds (less than paid amount)
4. **Audit Trail**: All refund requests are logged with timestamps and reasons
5. **Admin Dashboard**: Available in Django admin for comprehensive refund management

The system ensures students get quick refunds for incomplete sessions while protecting against abuse through manual review for completed sessions.
