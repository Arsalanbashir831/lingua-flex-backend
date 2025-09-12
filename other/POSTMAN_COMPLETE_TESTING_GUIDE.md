# 🚀 LinguaFlex Stripe Payment API - Complete Postman Testing Guide

## 📋 Overview
This guide provides step-by-step instructions for testing the LinguaFlex Stripe payment system using Postman. All endpoints, request formats, expected responses, and testing scenarios are covered.

## 🔧 Setup Requirements

### 1. Server Configuration
- **Base URL**: `http://127.0.0.1:8000`
- **Server Status**: ✅ Running on port 8000
- **Authentication**: Bearer Token required for most endpoints

### 2. Postman Environment Setup

Create a new environment in Postman with these variables:

```json
{
  "base_url": "http://127.0.0.1:8000",
  "api_base": "http://127.0.0.1:8000/api",
  "auth_token": "YOUR_BEARER_TOKEN_HERE",
  "student_token": "STUDENT_BEARER_TOKEN",
  "teacher_token": "TEACHER_BEARER_TOKEN",
  "admin_token": "ADMIN_BEARER_TOKEN"
}
```

### 3. Authentication Headers
For all authenticated requests, add:
```
Authorization: Bearer {{auth_token}}
Content-Type: application/json
```

---

## 🎯 Complete Testing Workflow

## **PHASE 1: Setup & Authentication**

### 1.1 Create Test Users
First, create test accounts (student, teacher, admin):

**Endpoint**: `POST {{api_base}}/auth/register/`
```json
{
  "email": "student@test.com",
  "password": "testpass123",
  "first_name": "Test",
  "last_name": "Student",
  "user_type": "student"
}
```

**Endpoint**: `POST {{api_base}}/auth/register/`
```json
{
  "email": "teacher@test.com",
  "password": "testpass123",
  "first_name": "Test",
  "last_name": "Teacher",
  "user_type": "teacher"
}
```

### 1.2 Login and Get Tokens
**Endpoint**: `POST {{api_base}}/auth/login/`
```json
{
  "email": "student@test.com",
  "password": "testpass123"
}
```

**Expected Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "student@test.com",
    "user_type": "student"
  }
}
```

⚠️ **Save the tokens in your Postman environment variables**

---

## **PHASE 2: Test Data Setup**

### 2.1 Create Teacher Profile & Gig
**Endpoint**: `POST {{api_base}}/accounts/teacher-profiles/`
**Headers**: `Authorization: Bearer {{teacher_token}}`
```json
{
  "bio": "Experienced English teacher",
  "languages": ["English", "Spanish"],
  "teaching_experience": 5,
  "hourly_rate": 25.00,
  "availability": "Flexible hours"
}
```

### 2.2 Create a Gig
**Endpoint**: `POST {{api_base}}/accounts/gigs/`
**Headers**: `Authorization: Bearer {{teacher_token}}`
```json
{
  "category": "language",
  "service_type": "Language Consultation",
  "service_title": "English Conversation Practice",
  "short_description": "Improve your English speaking skills",
  "full_description": "One-on-one conversation practice focused on fluency and confidence",
  "price_per_session": "25.00",
  "session_duration": 60,
  "tags": ["english", "conversation", "speaking"],
  "what_you_provide_in_session": [
    "Personalized feedback",
    "Grammar correction",
    "Pronunciation practice",
    "Confidence building"
  ],
  "status": "active"
}
```

### 2.3 Create Session Booking
**Endpoint**: `POST {{api_base}}/bookings/bookings/`
**Headers**: `Authorization: Bearer {{student_token}}`
```json
{
  "teacher": 2,
  "gig": 1,
  "start_time": "2024-12-20T10:00:00Z",
  "end_time": "2024-12-20T11:00:00Z",
  "notes": "Looking forward to improving my English"
}
```

**Note**: `duration_hours` and `scheduled_datetime` are auto-calculated from `start_time` and `end_time`.

### 2.4 Teacher Confirms Booking
**Endpoint**: `POST {{api_base}}/bookings/bookings/1/confirm/`
**Headers**: `Authorization: Bearer {{teacher_token}}`
```json
{}
```

---

## **PHASE 3: Payment Testing**

## 🔑 **Core Payment Endpoints**

### 3.1 Create Payment Intent (For Frontend Integration)
**Method**: `POST`
**URL**: `{{api_base}}/payments/create-payment-intent/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "session_booking_id": 1,
  "save_payment_method": true
}
```

**Expected Response**:
```json
{
  "success": true,
  "client_secret": "pi_3O1234567890_secret_abc123",
  "payment_id": 1,
  "amount_dollars": 25.00
}
```

**Note**: This creates a PaymentIntent that requires frontend (Stripe.js) to collect payment details.

### 3.1a Create Payment Intent with Test Payment Method (For API Testing)
**Method**: `POST`
**URL**: `{{api_base}}/payments/create-payment-intent/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "session_booking_id": 1,
  "payment_method_id": "pm_card_visa",
  "save_payment_method": true
}
```

**Expected Response**:
```json
{
  "success": true,
  "client_secret": "pi_3O1234567890_secret_abc123",
  "payment_id": 1,
  "amount_dollars": 25.00
}
```

**Available Test Payment Methods**:
- `pm_card_visa` - Visa test card
- `pm_card_mastercard` - Mastercard test card
- `pm_card_amex` - American Express test card
- `pm_card_decline` - Card that will be declined

**Test Cases**:
- ✅ Valid booking ID
- ❌ Invalid booking ID (should return 400)
- ❌ Already paid booking (should return 400)
- ❌ Unconfirmed booking (should return 400)

### 3.2 Create Payment Intent with Saved Card
**Method**: `POST`
**URL**: `{{api_base}}/payments/create-payment-intent/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "session_booking_id": 2,
  "payment_method_id": "pm_1O1234567890",
  "save_payment_method": false
}
```

### 3.3 Confirm Payment
**Method**: `POST`
**URL**: `{{api_base}}/payments/confirm-payment/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "payment_intent_id": "pi_3O1234567890"
}
```

**Expected Response**:
```json
{
  "success": true,
  "status": "succeeded",
  "requires_action": false,
  "client_secret": null
}
```

**⚠️ Important**: This endpoint only works if:
1. PaymentIntent was created WITH a payment_method_id, OR
2. A payment method was attached via frontend (Stripe.js)

**Common Error**: `"missing a payment method"` means you need to create the PaymentIntent with `payment_method_id` for API testing.

---

## 📊 **Payment Management Endpoints**

### 4.1 List All Payments
**Method**: `GET`
**URL**: `{{api_base}}/payments/payments/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Query Parameters** (optional):
- `?status=COMPLETED`
- `?limit=10`
- `?offset=0`

**Expected Response**:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "status": "COMPLETED",
      "amount_cents": 2500,
      "amount_dollars": 25.00,
      "currency": "USD",
      "student_email": "student@test.com",
      "teacher_email": "teacher@test.com",
      "teacher_name": "Test Teacher",
      "gig_title": "English Conversation Practice",
      "session_date": "2024-12-20T10:00:00Z",
      "created_at": "2024-12-15T14:30:00Z",
      "paid_at": "2024-12-15T14:35:00Z"
    }
  ]
}
```

### 4.2 Get Payment Details
**Method**: `GET`
**URL**: `{{api_base}}/payments/payments/1/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Expected Response**:
```json
{
  "id": 1,
  "status": "COMPLETED",
  "amount_cents": 2500,
  "amount_dollars": 25.00,
  "hourly_rate_cents": 2500,
  "hourly_rate_dollars": 25.00,
  "session_duration_hours": 1.0,
  "platform_fee_cents": 125,
  "currency": "USD",
  "payment_method_type": "card",
  "student_email": "student@test.com",
  "teacher_email": "teacher@test.com",
  "teacher_name": "Test Teacher",
  "gig_title": "English Conversation Practice",
  "session_date": "2024-12-20T10:00:00Z",
  "created_at": "2024-12-15T14:30:00Z",
  "paid_at": "2024-12-15T14:35:00Z",
  "updated_at": "2024-12-15T14:35:00Z"
}
```

---

## 💳 **Saved Payment Methods**

### 5.1 List Saved Payment Methods
**Method**: `GET`
**URL**: `{{api_base}}/payments/payment-methods/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Expected Response**:
```json
[
  {
    "id": 1,
    "stripe_payment_method_id": "pm_1O1234567890",
    "card_brand": "visa",
    "card_last_four": "4242",
    "card_exp_month": 12,
    "card_exp_year": 2025,
    "is_default": true,
    "display_name": "Visa ****4242 (Default)",
    "created_at": "2024-12-15T14:30:00Z"
  }
]
```

### 5.2 Save Payment Method
**Method**: `POST`
**URL**: `{{api_base}}/payments/payment-methods/save/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "payment_method_id": "pm_1O1234567890"
}
```

**Expected Response**:
```json
{
  "success": true,
  "payment_method": {
    "id": 2,
    "stripe_payment_method_id": "pm_1O1234567890",
    "card_brand": "mastercard",
    "card_last_four": "5555",
    "card_exp_month": 8,
    "card_exp_year": 2026,
    "is_default": false,
    "display_name": "Mastercard ****5555",
    "created_at": "2024-12-15T15:00:00Z"
  }
}
```

### 5.3 Delete Payment Method
**Method**: `DELETE`
**URL**: `{{api_base}}/payments/payment-methods/pm_1O1234567890/delete/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Expected Response**:
```json
{
  "success": true,
  "message": "Payment method deleted successfully"
}
```

---

## 🔄 **Refund System**

### 6.1 Create Refund Request
**Method**: `POST`
**URL**: `{{api_base}}/payments/refund-requests/`
**Headers**: `Authorization: Bearer {{student_token}}`

**Request Body**:
```json
{
  "payment_id": 1,
  "reason": "Session was cancelled by teacher at the last minute",
  "requested_amount_dollars": 25.00
}
```

**Expected Response**:
```json
{
  "id": 1,
  "reason": "Session was cancelled by teacher at the last minute",
  "requested_amount_cents": 2500,
  "requested_amount_dollars": 25.00,
  "status": "PENDING",
  "admin_notes": "",
  "payment_details": {
    "id": 1,
    "amount_dollars": 25.00,
    "teacher_name": "Test Teacher",
    "gig_title": "English Conversation Practice",
    "session_date": "2024-12-20T10:00:00Z"
  },
  "created_at": "2024-12-15T16:00:00Z",
  "reviewed_at": null,
  "refunded_at": null
}
```

### 6.2 List Refund Requests (Student View)
**Method**: `GET`
**URL**: `{{api_base}}/payments/refund-requests/`
**Headers**: `Authorization: Bearer {{student_token}}`

### 6.3 List All Refund Requests (Admin View)
**Method**: `GET`
**URL**: `{{api_base}}/payments/refund-requests/`
**Headers**: `Authorization: Bearer {{admin_token}}`

**Expected Response**:
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "reason": "Session was cancelled by teacher",
      "requested_amount_dollars": 25.00,
      "status": "PENDING",
      "admin_notes": "",
      "payment_details": {
        "id": 1,
        "amount_dollars": 25.00,
        "teacher_name": "Test Teacher",
        "teacher_email": "teacher@test.com",
        "gig_title": "English Conversation Practice",
        "session_date": "2024-12-20T10:00:00Z",
        "payment_date": "2024-12-15T14:35:00Z"
      },
      "student_details": {
        "id": 1,
        "name": "Test Student",
        "email": "student@test.com"
      },
      "created_at": "2024-12-15T16:00:00Z",
      "reviewed_at": null
    }
  ]
}
```

### 6.4 Admin Review Refund Request
**Method**: `PATCH`
**URL**: `{{api_base}}/payments/refund-requests/1/`
**Headers**: `Authorization: Bearer {{admin_token}}`

**Request Body (Approve)**:
```json
{
  "status": "APPROVED",
  "admin_notes": "Valid complaint. Teacher confirmed cancellation. Approved for full refund."
}
```

**Request Body (Reject)**:
```json
{
  "status": "REJECTED",
  "admin_notes": "Session was completed successfully. No grounds for refund."
}
```

### 6.5 Process Approved Refund
**Method**: `POST`
**URL**: `{{api_base}}/payments/refund-requests/1/process/`
**Headers**: `Authorization: Bearer {{admin_token}}`

**Request Body**: `{}` (empty)

**Expected Response**:
```json
{
  "success": true,
  "refund_id": "re_1O1234567890",
  "amount_refunded": 25.00
}
```

---

## 📈 **Admin Dashboard & Analytics**

### 7.1 Payment Dashboard
**Method**: `GET`
**URL**: `{{api_base}}/payments/dashboard/`
**Headers**: `Authorization: Bearer {{admin_token}}`

**Query Parameters** (optional):
- `?date_from=2024-12-01`
- `?date_to=2024-12-31`

**Expected Response**:
```json
{
  "total_payments": 25,
  "total_revenue_dollars": 625.00,
  "successful_payments": 23,
  "failed_payments": 2,
  "pending_refunds": 3,
  "recent_payments": [
    {
      "id": 1,
      "status": "COMPLETED",
      "amount_dollars": 25.00,
      "student_email": "student@test.com",
      "teacher_email": "teacher@test.com",
      "teacher_name": "Test Teacher",
      "gig_title": "English Conversation Practice",
      "session_date": "2024-12-20T10:00:00Z",
      "created_at": "2024-12-15T14:30:00Z"
    }
  ],
  "date_from": "2024-12-01",
  "date_to": "2024-12-31"
}
```

---

## 🔗 **Webhook Testing**

### 8.1 Stripe Webhook Endpoint
**Method**: `POST`
**URL**: `{{api_base}}/payments/webhooks/stripe/`
**Headers**: 
```
Content-Type: application/json
Stripe-Signature: t=1234567890,v1=signature_hash
```

**Test Event Body (Payment Success)**:
```json
{
  "id": "evt_1O1234567890",
  "object": "event",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_1O1234567890",
      "object": "payment_intent",
      "status": "succeeded",
      "amount": 2500,
      "currency": "usd",
      "charges": {
        "data": [
          {
            "id": "ch_1O1234567890"
          }
        ]
      }
    }
  }
}
```

---

## 🧪 **Complete Testing Scenarios**

### Scenario 1: Successful Payment Flow
1. Create session booking
2. Teacher confirms booking
3. Student creates payment intent
4. Student confirms payment
5. Verify payment status = COMPLETED

### Scenario 2: Refund Flow
1. Complete a payment
2. Student requests refund
3. Admin reviews and approves
4. Admin processes refund
5. Verify refund status = PROCESSED

### Scenario 3: Error Handling
1. Try to pay for unconfirmed booking (should fail)
2. Try to pay for already paid booking (should fail)
3. Try to create refund for unpaid booking (should fail)
4. Try to access other user's payments (should fail)

### Scenario 4: Saved Payment Methods
1. Save payment method during first payment
2. Use saved method for second payment
3. List saved methods
4. Delete a saved method

---

## 🔧 **Postman Collection Setup**

### Import This JSON Collection:

```json
{
  "info": {
    "name": "LinguaFlex Stripe Payments",
    "description": "Complete test collection for LinguaFlex payment system"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "http://127.0.0.1:8000"
    },
    {
      "key": "api_base",
      "value": "http://127.0.0.1:8000/api"
    }
  ],
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{auth_token}}"
      }
    ]
  }
}
```

---

## 📋 **Testing Checklist**

### ✅ Pre-Testing Setup
- [ ] Server running on http://127.0.0.1:8000
- [ ] Postman environment configured
- [ ] Test users created (student, teacher, admin)
- [ ] Authentication tokens obtained
- [ ] Test gig and booking created

### ✅ Payment Flow Testing
- [ ] Create payment intent (valid booking)
- [ ] Create payment intent (invalid scenarios)
- [ ] Confirm payment
- [ ] List payments
- [ ] Get payment details

### ✅ Payment Methods Testing
- [ ] Save payment method
- [ ] List saved payment methods
- [ ] Delete payment method

### ✅ Refund System Testing
- [ ] Create refund request
- [ ] List refund requests (student view)
- [ ] List refund requests (admin view)
- [ ] Admin approve/reject refund
- [ ] Process approved refund

### ✅ Admin Dashboard Testing
- [ ] Access payment dashboard
- [ ] Filter by date range
- [ ] Verify analytics data

### ✅ Error Handling Testing
- [ ] Unauthorized access attempts
- [ ] Invalid payment scenarios
- [ ] Malformed requests
- [ ] Authentication failures

---

## 🚨 **Common Test Issues & Solutions**

### Issue: 401 Unauthorized
**Solution**: Check your Bearer token is valid and not expired

### Issue: 400 Bad Request - Booking not confirmed
**Solution**: Ensure teacher has confirmed the booking first

### Issue: 400 Bad Request - Already paid
**Solution**: Use a different booking that hasn't been paid for

### Issue: CORS errors
**Solution**: Ensure frontend domain is in CORS_ALLOWED_ORIGINS

### Issue: Webhook signature verification failed
**Solution**: Use proper Stripe-Signature header with valid signature

---

## 📊 **Expected Test Results Summary**

| Test Category | Total Tests | Expected Pass | Critical Issues |
|---------------|-------------|---------------|-----------------|
| Authentication | 6 | 6 | None |
| Payment Creation | 8 | 6 | 2 expected failures |
| Payment Management | 4 | 4 | None |
| Saved Methods | 6 | 6 | None |
| Refund System | 10 | 10 | None |
| Admin Dashboard | 4 | 4 | None |
| Error Handling | 12 | 12 | None (all should fail as expected) |
| **TOTAL** | **50** | **48** | **2 expected failures** |

---

## 🎯 **Success Criteria**
- ✅ All payment flows work end-to-end
- ✅ Admin can manage refunds
- ✅ Proper error handling for edge cases
- ✅ Security measures prevent unauthorized access
- ✅ Payment analytics display correctly

**Your Stripe payment system is ready for comprehensive testing!** 🚀

---

*Last Updated: September 9, 2025*
*Testing Environment: Development Server (localhost:8000)*
