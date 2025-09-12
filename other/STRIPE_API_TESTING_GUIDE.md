# LinguaFlex Stripe Payment API Testing Guide

## Overview
This guide covers testing the complete Stripe payment integration for the LinguaFlex language learning platform.

## Prerequisites
1. Set up environment variables (see `STRIPE_ENVIRONMENT_SETUP.md`)
2. Create a teacher account and publish a gig
3. Create a student account
4. Have test card numbers ready from Stripe documentation

## API Endpoints

### 1. Create Payment Intent
**POST** `/api/payments/create-payment-intent/`

Creates a Stripe PaymentIntent for a session booking.

**Headers:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
    "session_booking_id": 1,
    "payment_method_id": "pm_card_visa",
    "save_payment_method": true
}
```

**Response:**
```json
{
    "success": true,
    "client_secret": "pi_xxx_secret_xxx",
    "payment_id": 1,
    "amount_dollars": 25.00
}
```

### 2. Confirm Payment
**POST** `/api/payments/confirm-payment/`

Confirms a PaymentIntent after client-side confirmation.

**Body:**
```json
{
    "payment_intent_id": "pi_xxx"
}
```

### 3. List Payments
**GET** `/api/payments/payments/`

Lists all payments for the authenticated user.

**Query Parameters:**
- `status`: Filter by payment status
- `limit`: Number of results per page

### 4. Save Payment Method
**POST** `/api/payments/payment-methods/save/`

Saves a payment method for future use.

**Body:**
```json
{
    "payment_method_id": "pm_card_visa"
}
```

### 5. List Saved Payment Methods
**GET** `/api/payments/payment-methods/`

Lists all saved payment methods for the authenticated user.

### 6. Create Refund Request
**POST** `/api/payments/refund-requests/`

Creates a refund request for a completed payment.

**Body:**
```json
{
    "payment_id": 1,
    "reason": "Session was cancelled by teacher",
    "requested_amount_dollars": 25.00
}
```

### 7. Admin - Payment Dashboard
**GET** `/api/payments/dashboard/`

Admin-only endpoint for payment analytics.

**Query Parameters:**
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

## Testing Scenarios

### Scenario 1: Successful Payment Flow

1. **Create a session booking:**
```bash
POST /api/bookings/bookings/
{
    "teacher": 2,
    "gig": 1,
    "start_time": "2024-12-20T10:00:00Z",
    "end_time": "2024-12-20T11:00:00Z",
    "duration_hours": 1.0,
    "scheduled_datetime": "2024-12-20T10:00:00Z"
}
```

2. **Teacher confirms the booking:**
```bash
POST /api/bookings/bookings/1/confirm/
```

3. **Student creates payment intent:**
```bash
POST /api/payments/create-payment-intent/
{
    "session_booking_id": 1,
    "save_payment_method": true
}
```

4. **Use client_secret on frontend with Stripe.js**

5. **Confirm payment:**
```bash
POST /api/payments/confirm-payment/
{
    "payment_intent_id": "pi_xxx"
}
```

### Scenario 2: Payment with Saved Card

1. **Use saved payment method:**
```bash
POST /api/payments/create-payment-intent/
{
    "session_booking_id": 2,
    "payment_method_id": "pm_xxx"
}
```

### Scenario 3: Refund Flow

1. **Student requests refund:**
```bash
POST /api/payments/refund-requests/
{
    "payment_id": 1,
    "reason": "Session quality was poor",
    "requested_amount_dollars": 25.00
}
```

2. **Admin reviews refund:**
```bash
PATCH /api/payments/refund-requests/1/
{
    "status": "APPROVED",
    "admin_notes": "Valid complaint, approved for full refund"
}
```

3. **Admin processes refund:**
```bash
POST /api/payments/refund-requests/1/process/
```

## Test Cards

Use these Stripe test card numbers:

- **Visa:** 4242424242424242
- **Visa (debit):** 4000056655665556
- **Mastercard:** 5555555555554444
- **American Express:** 378282246310005
- **Declined card:** 4000000000000002
- **3D Secure:** 4000002500003155

## Webhooks Testing

1. **Install Stripe CLI:**
```bash
stripe login
stripe listen --forward-to localhost:8000/api/payments/webhooks/stripe/
```

2. **Trigger test events:**
```bash
stripe trigger payment_intent.succeeded
stripe trigger payment_intent.payment_failed
```

## Error Scenarios

### Invalid Session Booking
```bash
POST /api/payments/create-payment-intent/
{
    "session_booking_id": 999
}
```
**Expected:** 400 Bad Request

### Payment for Unconfirmed Booking
```bash
POST /api/payments/create-payment-intent/
{
    "session_booking_id": 1
}
```
**Expected:** 400 Bad Request (if booking status is PENDING)

### Duplicate Payment
```bash
POST /api/payments/create-payment-intent/
{
    "session_booking_id": 1
}
```
**Expected:** 400 Bad Request (if already paid)

## Admin Testing

### Payment Dashboard
```bash
GET /api/payments/dashboard/?date_from=2024-12-01&date_to=2024-12-31
```

### Refund Management
```bash
GET /api/payments/refund-requests/
PATCH /api/payments/refund-requests/1/
POST /api/payments/refund-requests/1/process/
```

## Integration Testing Tips

1. **Use Postman or similar tools** for manual API testing
2. **Set up proper authentication** with Bearer tokens
3. **Test edge cases** like network failures, expired cards
4. **Monitor Stripe Dashboard** for payment events
5. **Check Django admin** for data consistency
6. **Test webhooks** with Stripe CLI
7. **Verify email notifications** (if implemented)

## Common Issues

### CORS Errors
Ensure your frontend domain is in `CORS_ALLOWED_ORIGINS` in settings.py

### Webhook Signature Verification Failed
Check that `STRIPE_WEBHOOK_SECRET` matches your Stripe webhook secret

### Payment Intent Already Confirmed
This happens when trying to confirm the same payment twice

### Invalid Payment Method
Ensure payment methods are properly attached to customers

## Next Steps

1. **Frontend Integration:** Use Stripe.js or React Stripe.js
2. **Email Notifications:** Send payment confirmations
3. **Invoice Generation:** Create PDF invoices
4. **Recurring Payments:** For subscription-based services
5. **Multi-party Payments:** Split payments between platform and teachers
