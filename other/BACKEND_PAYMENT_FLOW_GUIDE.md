# Backend-Only Payment Flow Guide

## Overview
This guide covers the complete backend-only payment flow where students can add payment methods, save cards, and process payments entirely through backend API endpoints (no frontend JavaScript required).

## Authentication
All endpoints require authentication. Include in headers:
```
Authorization: Bearer <your_jwt_token>
```

## Flow 1: Add Payment Method (Save Card for Future Use)

### Endpoint: Add Payment Method
```
POST /api/payments/add-payment-method/
```

**Request Body:**
```json
{
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "cardholder_name": "John Doe",
    "save_for_future": true
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Payment method added successfully",
    "payment_method_id": "pm_1234567890",
    "card_last4": "4242",
    "card_brand": "visa",
    "saved": true
}
```

**Response (Error):**
```json
{
    "success": false,
    "error": "Your card was declined.",
    "details": {
        "decline_code": "generic_decline",
        "param": "card_number"
    }
}
```

## Flow 2: Process Payment with New Card

### Endpoint: Process Payment
```
POST /api/payments/process-payment/
```

**Request Body (New Card):**
```json
{
    "gig_id": 1,
    "card_details": {
        "card_number": "4242424242424242",
        "exp_month": 12,
        "exp_year": 2025,
        "cvc": "123",
        "cardholder_name": "Jane Smith"
    },
    "save_card": true
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Payment processed successfully",
    "payment_id": 123,
    "payment_intent_id": "pi_1234567890",
    "amount": 50.00,
    "currency": "usd",
    "status": "succeeded",
    "booking_id": 456,
    "payment_method_saved": true
}
```

## Flow 3: Process Payment with Saved Card

### First, get saved payment methods:
```
GET /api/payments/payment-methods/
```

**Response:**
```json
{
    "results": [
        {
            "id": 1,
            "stripe_payment_method_id": "pm_1234567890",
            "card_last4": "4242",
            "card_brand": "visa",
            "card_exp_month": 12,
            "card_exp_year": 2025,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

### Then process payment with saved card:
```
POST /stripe-payments/process-payment/
```

**Request Body (Saved Card):**
```json
{
    "gig_id": 1,
    "saved_payment_method_id": "pm_1234567890"
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Payment processed successfully",
    "payment_id": 124,
    "payment_intent_id": "pi_0987654321",
    "amount": 75.00,
    "currency": "usd",
    "status": "succeeded",
    "booking_id": 457,
    "used_saved_card": true
}
```

## Error Handling

### Common Error Responses:

**Card Declined:**
```json
{
    "success": false,
    "error": "Your card was declined.",
    "details": {
        "decline_code": "insufficient_funds",
        "param": "card_number"
    }
}
```

**Invalid Card:**
```json
{
    "success": false,
    "error": "Your card number is invalid.",
    "details": {
        "code": "card_declined",
        "param": "card_number"
    }
}
```

**Gig Not Available:**
```json
{
    "success": false,
    "error": "Gig is not available for booking"
}
```

**Missing Payment Method:**
```json
{
    "success": false,
    "error": "Either card_details or saved_payment_method_id must be provided"
}
```

## Test Cards

Use these test cards for different scenarios:

| Card Number | Brand | Description |
|-------------|-------|-------------|
| 4242424242424242 | Visa | Succeeds |
| 4000000000000002 | Visa | Declined |
| 4000000000009995 | Visa | Insufficient funds |
| 4000000000009987 | Visa | Lost card |
| 4000000000009979 | Visa | Stolen card |
| 5555555555554444 | Mastercard | Succeeds |
| 378282246310005 | American Express | Succeeds |

## Business Logic

1. **Pre-payment Required**: All gigs must be paid before booking is confirmed
2. **Admin Account**: 10% goes to admin, 90% to teacher
3. **USD Only**: All payments processed in USD
4. **Teacher Confirmation**: Teachers must confirm before lessons begin
5. **Refund Workflow**: Students can request refunds through admin

## Security Features

1. **Card Data Security**: Card details are sent directly to Stripe, never stored locally
2. **PCI Compliance**: Using Stripe's secure tokenization
3. **Authentication**: All endpoints require valid JWT tokens
4. **Rate Limiting**: Prevents payment abuse
5. **Webhook Verification**: Stripe webhooks are verified for authenticity

## Complete Flow Example

### Step 1: Student adds a payment method
```bash
curl -X POST http://localhost:8000/api/payments/add-payment-method/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "cardholder_name": "John Doe",
    "save_for_future": true
  }'
```

### Step 2: Student books and pays for a gig
```bash
curl -X POST http://localhost:8000/api/payments/process-payment/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gig_id": 1,
    "saved_payment_method_id": "pm_1234567890"
  }'
```

### Step 3: Check payment status
```bash
curl -X GET http://localhost:8000/api/payments/payments/123/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Postman Collection

Import the updated `LinguaFlex_Backend_Payments.postman_collection.json` file to test all these endpoints with pre-configured requests.

## Environment Variables for Postman

```json
{
  "base_url": "http://localhost:8000",
  "jwt_token": "YOUR_JWT_TOKEN_HERE",
  "test_gig_id": "1",
  "test_card_number": "4242424242424242",
  "test_exp_month": "12",
  "test_exp_year": "2025",
  "test_cvc": "123"
}
```
