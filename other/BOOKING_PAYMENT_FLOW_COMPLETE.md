# 🔄 Complete Booking & Payment Flow Documentation

## Overview
This document describes the complete implementation of the booking and payment system where students create booking sessions against teacher gigs and then process payments using card data.

## 🎯 Workflow Implementation

### **Phase 1: Student Creates Booking Session**

#### Endpoint: Create Booking
**POST** `/api/bookings/bookings/`

**Headers:**
```json
{
  "Authorization": "Bearer STUDENT_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "teacher": "{{teacher_id}}",
  "gig": 11,
  "start_time": "2024-12-20T10:00:00Z",
  "end_time": "2024-12-20T10:30:00Z",
  "notes": "Looking forward to improving my English"
}
```

**Success Response (201):**
```json
{
  "id": 123,
  "teacher": 5,
  "gig": 11,
  "student": 15,
  "start_time": "2024-12-20T10:00:00Z",
  "end_time": "2024-12-20T10:30:00Z",
  "duration_hours": 0.5,
  "status": "PENDING",
  "payment_status": "UNPAID",
  "notes": "Looking forward to improving my English",
  "created_at": "2024-12-20T09:00:00Z"
}
```

---

### **Phase 2: Student Processes Payment**

#### Endpoint: Process Booking Payment
**POST** `/api/payments/process-booking-payment/`

**Headers:**
```json
{
  "Authorization": "Bearer STUDENT_JWT_TOKEN",
  "Content-Type": "application/json"
}
```

**Request Body (New Card):**
```json
{
  "booking_id": 123,
  "card_number": "4242424242424242",
  "exp_month": 12,
  "exp_year": 2025,
  "cvc": "123",
  "cardholder_name": "Student Name",
  "save_payment_method": true
}
```

**Request Body (Saved Card):**
```json
{
  "booking_id": 123,
  "saved_payment_method_id": "pm_1234567890"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Payment processed successfully",
  "payment_intent_id": "pi_1234567890",
  "booking_id": 123,
  "payment_id": 456,
  "amount_paid": 26.25,
  "session_cost": 25.0,
  "platform_fee": 1.25,
  "duration_hours": 0.5,
  "hourly_rate": 50.0,
  "status": "succeeded",
  "card_last4": "4242",
  "card_brand": "visa",
  "zoom_join_url": "https://zoom.us/j/123456789",
  "booking_details": {
    "start_time": "2024-12-20T10:00:00Z",
    "end_time": "2024-12-20T10:30:00Z",
    "teacher_name": "John Teacher",
    "gig_title": "English Conversation Practice"
  }
}
```

---

## 💰 Payment Calculation Logic

### Automatic Calculation
The system automatically calculates:

1. **Duration**: Calculated from `start_time` and `end_time`
   ```python
   duration_hours = (end_time - start_time).total_seconds() / 3600
   ```

2. **Session Cost**: Based on gig's hourly rate
   ```python
   session_cost = gig.price_per_session * duration_hours
   ```

3. **Platform Fee**: 5% minimum $1.00
   ```python
   platform_fee = max(session_cost * 0.05, 1.00)
   ```

4. **Total Amount**: Session cost + Platform fee
   ```python
   total_amount = session_cost + platform_fee
   ```

### Example Calculation
- **Gig Rate**: $50/hour
- **Session Duration**: 0.5 hours (30 minutes)
- **Session Cost**: $50 × 0.5 = $25.00
- **Platform Fee**: max($25.00 × 0.05, $1.00) = $1.25
- **Total Payment**: $25.00 + $1.25 = **$26.25**

---

## 🔄 Status Flow

### Booking Status Flow
```
PENDING → CONFIRMED (after successful payment)
   ↓
CANCELLED (if payment fails or manual cancellation)
```

### Payment Status Flow
```
UNPAID → PENDING → PAID
   ↓        ↓       ↓
FAILED   FAILED   REFUNDED
```

### Complete Flow States

| Step | Booking Status | Payment Status | Description |
|------|----------------|----------------|-------------|
| 1 | PENDING | UNPAID | Booking created, awaiting payment |
| 2 | PENDING | PENDING | Payment processing |
| 3 | CONFIRMED | PAID | Payment successful, session ready |
| X | CANCELLED | FAILED | Payment failed |

---

## 🧪 Testing

### Test Credentials
```json
{
  "student": {
    "email": "fahije3853@hostbyt.com",
    "password": "testpassword1234"
  },
  "teacher": {
    "email": "rebin81412@hostbyt.com",
    "password": "testpassword123"
  }
}
```

### Test Cards
| Card Number | Type | Expected Result |
|-------------|------|-----------------|
| 4242424242424242 | Visa | Success |
| 4000000000000002 | Visa | Declined |
| 5555555555554444 | Mastercard | Success |
| 378282246310005 | Amex | Success |

### Run Complete Test
```bash
python test_booking_payment_flow.py
```

This will:
1. Login as student
2. Get available gigs
3. Create a booking session
4. Process payment for the booking
5. Verify complete flow

---

## 🔐 Security Features

### Validation Checks
1. **Booking Ownership**: Only booking owner can pay
2. **Booking Status**: Cannot pay for cancelled bookings
3. **Payment Status**: Cannot pay twice for same booking
4. **Gig Availability**: Gig must be active
5. **Card Security**: Uses Stripe's secure payment methods

### Payment Security
1. **No Raw Card Storage**: Cards tokenized via Stripe
2. **PCI Compliance**: Using Stripe's secure infrastructure
3. **Idempotency**: Prevents duplicate payments
4. **Customer Verification**: Links payments to authenticated users

---

## 📊 Database Integration

### Models Updated
1. **SessionBooking**: Gets payment_status and status updates
2. **Payment**: Created with complete payment details
3. **SavedPaymentMethod**: Optionally saves cards for future use
4. **StripeCustomer**: Links users to Stripe customers

### Automatic Actions
1. **Zoom Meeting**: Created automatically after successful payment
2. **Email Notifications**: Sent to both student and teacher
3. **Payment Records**: Complete audit trail maintained
4. **Status Updates**: Real-time status tracking

---

## 🚀 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bookings/bookings/` | POST | Create booking session |
| `/api/payments/process-booking-payment/` | POST | Pay for existing booking |
| `/api/payments/add-payment-method/` | POST | Save payment method |
| `/api/payments/payment-methods/` | GET | List saved payment methods |

---

## 🎉 Complete Example

### Step 1: Create Booking
```bash
curl -X POST http://localhost:8000/api/bookings/bookings/ \
  -H "Authorization: Bearer student_token" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher": 5,
    "gig": 11,
    "start_time": "2024-12-20T10:00:00Z",
    "end_time": "2024-12-20T10:30:00Z",
    "notes": "English conversation practice"
  }'
```

### Step 2: Process Payment
```bash
curl -X POST http://localhost:8000/api/payments/process-booking-payment/ \
  -H "Authorization: Bearer student_token" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 123,
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "cardholder_name": "Student Name",
    "save_payment_method": true
  }'
```

### Result
- ✅ Booking confirmed and paid
- ✅ Zoom meeting created
- ✅ Payment method saved (if requested)
- ✅ Teacher and student notified
- ✅ Ready for language session!

This implementation provides a complete, secure, and user-friendly booking and payment system for the LinguaFlex platform.
