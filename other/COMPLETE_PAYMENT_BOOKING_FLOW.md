# 🔄 Complete Payment Flow for Booking Sessions

## Overview
This document provides a comprehensive flow of how payments are processed against booking sessions in the LinguaFlex platform.

## 📋 Payment Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   1. BOOKING    │───▶│   2. PAYMENT    │───▶│ 3. CONFIRMATION │───▶│  4. EXECUTION   │
│     CREATION    │    │    PROCESSING   │    │   & VALIDATION  │    │   & TRACKING    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Complete Payment Workflow

### **Phase 1: Pre-Payment Setup**

#### Step 1.1: Student Creates Session Booking
**Endpoint:** `POST /api/bookings/bookings/`

```json
{
  "teacher": 2,
  "gig": 1,
  "start_time": "2024-12-20T10:00:00Z",
  "end_time": "2024-12-20T11:00:00Z",
  "duration_hours": 1.0,
  "scheduled_datetime": "2024-12-20T10:00:00Z"
}
```

**Result:** Creates `SessionBooking` with status `PENDING` and payment_status `UNPAID`

#### Step 1.2: Teacher Confirms Booking
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/confirm/`

**Result:** Updates booking status to `CONFIRMED`, payment_status remains `UNPAID`

---

### **Phase 2: Payment Processing**

#### Step 2.1: Create Payment Intent
**Endpoint:** `POST /api/payments/create-payment-intent/`

```json
{
  "session_booking_id": 1,
  "payment_method_id": "pm_card_visa",  // Optional: use saved payment method
  "save_payment_method": true          // Optional: save for future use
}
```

**Backend Process:**
1. **Validate Booking:** Check if booking exists and is confirmed
2. **Calculate Amount:** 
   - Base amount = `gig.price_per_session * duration_hours`
   - Platform fee = 5% (minimum $1.00)
   - Total amount = Base + Platform fee
3. **Get/Create Stripe Customer:** Link user to Stripe customer ID
4. **Create Stripe PaymentIntent:**
   ```python
   intent_params = {
       'amount': total_amount_cents,
       'currency': 'usd',
       'customer': customer.stripe_customer_id,
       'metadata': {
           'session_booking_id': session_booking.id,
           'teacher_id': session_booking.teacher.id,
           'student_id': session_booking.student.id,
           'gig_id': gig.id,
       }
   }
   ```
5. **Create Payment Record:** Save payment in `PENDING` status

**Response:**
```json
{
  "success": true,
  "client_secret": "pi_1234567890_secret_abcdef",
  "payment_id": 123,
  "amount_dollars": 52.50
}
```

#### Step 2.2: Confirm Payment
**Endpoint:** `POST /api/payments/confirm-payment/`

```json
{
  "payment_intent_id": "pi_1234567890",
  "payment_method_id": "pm_card_visa"
}
```

**Backend Process:**
1. **Retrieve PaymentIntent:** Get from Stripe using payment_intent_id
2. **Confirm Payment:** Execute the payment with Stripe
3. **Update Records:**
   - Payment status → `COMPLETED`
   - SessionBooking payment_status → `PAID`
   - SessionBooking status → `CONFIRMED` (if not already)

**Response:**
```json
{
  "success": true,
  "payment_intent_id": "pi_1234567890",
  "status": "succeeded",
  "amount": 5250,
  "currency": "usd"
}
```

---

### **Phase 3: Alternative Payment Methods**

#### Option A: #### Process Payment with New Card

**Updated Flow - 3 Steps Required:**

1. **Student Creates Booking** (Status: PENDING, Payment: UNPAID)
2. **Teacher Confirms Booking** (Status: CONFIRMED, Payment: UNPAID) 
3. **Student Pays for Booking** (Status: CONFIRMED, Payment: PAID)

**Step 1: Student Creates Booking**
**Endpoint:** `POST /api/bookings/bookings/`

```json
{
  "teacher": 2,
  "gig": 11,
  "start_time": "2024-12-20T10:00:00Z",
  "end_time": "2024-12-20T10:30:00Z",
  "notes": "Looking forward to improving my English"
}
```

**Response:**
```json
{
  "id": 61,
  "status": "PENDING",
  "payment_status": "UNPAID",
  "duration_hours": 0.5
}
```

**Step 2: Teacher Confirms Booking**
**Endpoint:** `POST /api/bookings/bookings/{booking_id}/confirm/`

```json
{
  "message": "Booking confirmed successfully",
  "booking": {
    "id": 61,
    "status": "CONFIRMED",
    "payment_status": "UNPAID",
    "zoom_meeting_id": "123456789",
    "zoom_join_url": "https://zoom.us/j/123456789"
  }
}
```

**Step 3: Student Pays for Confirmed Booking**
**Endpoint:** `POST /api/payments/process-booking-payment/`

```json
{
  "booking_id": 61,
  "card_number": "4242424242424242",
  "exp_month": 12,
  "exp_year": 2025,
  "cvc": "123",
  "cardholder_name": "Student Name",
  "save_payment_method": true
}
```

**Payment Validation:**
- ✅ Booking must exist and belong to student
- ✅ Booking must be CONFIRMED by teacher
- ✅ Booking must not already be PAID
- ✅ Booking must not be CANCELLED
- ✅ Gig must still be active

**Response:**
```json
{
  "success": true,
  "message": "Payment processed successfully",
  "payment_intent_id": "pi_1234567890",
  "booking_id": 61,
  "amount_paid": 26.25,
  "session_cost": 25.00,
  "platform_fee": 1.25,
  "status": "succeeded",
  "card_last4": "4242",
  "card_brand": "visa"
}
```

**Final Booking Status:**
- Status: `CONFIRMED`
- Payment Status: `PAID`
- Zoom meeting ready for session
**Endpoint:** `POST /api/payments/add-payment-method/`

```json
{
  "card_number": "4242424242424242",
  "exp_month": 12,
  "exp_year": 2025,
  "cvc": "123",
  "cardholder_name": "Student Name",
  "save_for_future": true
}
```

Then use returned `payment_method_id` in payment intent creation.

#### Option B: Process Payment with Saved Card
**Endpoint:** `GET /api/payments/payment-methods/`

Get saved payment methods, then use `stripe_payment_method_id` in payment processing.

---

## 💰 Payment Calculation Logic

### Pricing Structure
```python
def calculate_payment_amount(gig, duration_hours):
    # Base calculation
    hourly_rate = gig.price_per_session  # e.g., $50.00
    session_cost = hourly_rate * duration_hours  # e.g., $50.00 * 1.0 = $50.00
    
    # Platform fee (5% minimum $1.00)
    platform_fee = max(session_cost * 0.05, 1.00)  # e.g., $2.50
    
    # Total amount
    total_amount = session_cost + platform_fee  # e.g., $52.50
    
    return {
        'session_cost': session_cost,
        'platform_fee': platform_fee,
        'total_amount': total_amount
    }
```

### Payment Distribution
- **Student Pays:** Total amount (session cost + platform fee)
- **Platform Receives:** Platform fee (5% minimum $1.00)  
- **Teacher Receives:** Session cost (95% after fee)

---

## 🔄 Database Models Integration

### SessionBooking Model
```python
class SessionBooking(models.Model):
    student = models.ForeignKey(User, related_name='booked_sessions')
    teacher = models.ForeignKey(User, related_name='teaching_sessions')
    gig = models.ForeignKey('accounts.Gig', related_name='bookings')
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Status tracking
    status = models.CharField(choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    
    # Zoom integration
    zoom_meeting_id = models.CharField(max_length=500, blank=True)
    zoom_join_url = models.URLField(max_length=500, blank=True)
```

### Payment Model
```python
class Payment(models.Model):
    session_booking = models.OneToOneField(
        'bookings.SessionBooking', 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    student = models.ForeignKey(User, related_name='payments_made')
    teacher = models.ForeignKey(User, related_name='payments_received')
    gig = models.ForeignKey('accounts.Gig', related_name='payments')
    
    # Stripe details
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True)
    
    # Payment amounts (in cents)
    amount_cents = models.IntegerField()
    hourly_rate_cents = models.IntegerField()
    platform_fee_cents = models.IntegerField()
    
    # Status and metadata
    status = models.CharField(choices=STATUS_CHOICES, default='PENDING')
    currency = models.CharField(max_length=3, default='USD')
```

---

## 🚀 Complete Flow Example

### Example: Student Books and Pays for 1.5-hour Spanish Lesson

**Step 1: Create Booking**
```bash
curl -X POST http://localhost:8000/api/bookings/bookings/ \
  -H "Authorization: Bearer student_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher": 5,
    "gig": 12,
    "start_time": "2024-12-25T14:00:00Z",
    "end_time": "2024-12-25T15:30:00Z", 
    "duration_hours": 1.5
  }'
```

**Step 2: Teacher Confirms**
```bash
curl -X POST http://localhost:8000/api/bookings/bookings/45/confirm/ \
  -H "Authorization: Bearer teacher_jwt_token"
```

**Step 3: Student Creates Payment Intent**
```bash
curl -X POST http://localhost:8000/api/payments/create-payment-intent/ \
  -H "Authorization: Bearer student_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_booking_id": 45,
    "save_payment_method": true
  }'
```

**Response:**
```json
{
  "success": true,
  "client_secret": "pi_1ABC123_secret_xyz789",
  "payment_id": 67,
  "amount_dollars": 78.75
}
```

**Calculation:**
- Gig price: $50/hour
- Duration: 1.5 hours  
- Session cost: $50 × 1.5 = $75.00
- Platform fee: $75.00 × 0.05 = $3.75
- **Total: $78.75**

**Step 4: Student Confirms Payment**
```bash
curl -X POST http://localhost:8000/api/payments/confirm-payment/ \
  -H "Authorization: Bearer student_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_intent_id": "pi_1ABC123",
    "payment_method_id": "pm_card_visa"
  }'
```

**Final State:**
- SessionBooking: `status='CONFIRMED'`, `payment_status='PAID'`
- Payment: `status='COMPLETED'`
- Stripe PaymentIntent: `status='succeeded'`

---

## 🔐 Security & Validation

### Pre-Payment Validation
1. **Booking exists** and belongs to the student
2. **Booking is confirmed** by teacher
3. **No existing payment** for this booking
4. **Valid gig** with active pricing
5. **User authentication** via JWT

### Payment Processing Security
1. **Stripe tokenization** - No raw card data stored
2. **Idempotency keys** - Prevent duplicate payments  
3. **Webhook verification** - Validate Stripe events
4. **Amount validation** - Server-side calculation
5. **Customer verification** - Link payments to users

### Post-Payment Actions
1. **Status updates** - Booking and payment records
2. **Zoom meeting creation** - Automatic meeting setup
3. **Email notifications** - Confirmation to both parties
4. **Webhook handling** - Process Stripe events
5. **Refund eligibility** - Track refund status

---

## 🧪 Testing the Complete Flow

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

### Test Script
```bash
# Run complete booking and payment test
python test_complete_booking_payment_flow.py
```

### Test Cards
- **Success:** 4242424242424242
- **Declined:** 4000000000000002  
- **Insufficient Funds:** 4000000000009995

---

## 📊 Payment Status Tracking

### SessionBooking Payment Status Flow
```
UNPAID → PENDING → PAID
   ↓        ↓       ↓
FAILED   FAILED   REFUNDED
```

### Payment Status Flow  
```
PENDING → PROCESSING → COMPLETED
   ↓          ↓           ↓
FAILED     FAILED    REFUNDED
```

### Integration Points
- **Booking Creation** → Payment status = `UNPAID`
- **Payment Intent** → Payment status = `PENDING`
- **Payment Success** → Both statuses = `PAID`/`COMPLETED`
- **Payment Failure** → Both statuses = `FAILED`
- **Refund Processed** → Both statuses = `REFUNDED`

---

## 🎉 Summary

The payment flow integrates seamlessly with the booking system:

1. **📅 Booking Created** → Student creates session booking
2. **✅ Teacher Confirms** → Booking becomes payable  
3. **💳 Payment Intent** → Stripe payment intent created
4. **💰 Payment Confirmed** → Money processed, booking finalized
5. **🎓 Session Ready** → Zoom meeting created, notifications sent

The system ensures **no lesson can start without payment**, maintaining platform revenue and teacher compensation security.
