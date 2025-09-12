# 📋 LinguaFlex Stripe Payment API - Postman Testing Checklist

## 🚀 Quick Start Guide

### 1. Import Files to Postman
- **Collection**: Import `LinguaFlex_Stripe_Payments.postman_collection.json`
- **Environment**: Import `LinguaFlex_Stripe_Environment.postman_environment.json`

### 2. Server Setup
✅ **Verify server is running**: http://127.0.0.1:8000
```bash
python manage.py runserver
```

### 3. Environment Configuration
Update these variables in your Postman environment:
- `student_token`: Get from login response
- `teacher_token`: Get from login response  
- `admin_token`: Get from admin login
- `stripe_publishable_key`: Your Stripe test key

---

## 📝 **PHASE 1: Pre-Testing Setup**

### ✅ Authentication Setup
- [ ] **Register Student**: `POST /auth/register/` (student@test.com)
- [ ] **Register Teacher**: `POST /auth/register/` (teacher@test.com)
- [ ] **Login Student**: `POST /auth/login/` → Save token to `student_token`
- [ ] **Login Teacher**: `POST /auth/login/` → Save token to `teacher_token`
- [ ] **Login Admin**: `POST /auth/login/` → Save token to `admin_token`

### ✅ Test Data Creation
- [ ] **Create Teacher Profile**: `POST /accounts/teacher-profiles/`
- [ ] **Create Gig**: `POST /accounts/gigs/` → Note gig ID
- [ ] **Create Booking**: `POST /bookings/bookings/` → Note booking ID
- [ ] **Confirm Booking**: `POST /bookings/bookings/{id}/confirm/`

---

## 📝 **PHASE 2: Payment System Testing**

### ✅ Core Payment Flow
- [ ] **Create Payment Intent**: `POST /payments/create-payment-intent/`
  - Expected: 201 Created with `client_secret`
  - Save `payment_id` for later tests
- [ ] **Confirm Payment**: `POST /payments/confirm-payment/`
  - Expected: 200 OK with `success: true`
- [ ] **List Payments**: `GET /payments/payments/`
  - Expected: 200 OK with payment list
- [ ] **Get Payment Details**: `GET /payments/payments/{id}/`
  - Expected: 200 OK with payment details

### ✅ Saved Payment Methods
- [ ] **Save Payment Method**: `POST /payments/payment-methods/save/`
  - Expected: 201 Created with method details
- [ ] **List Payment Methods**: `GET /payments/payment-methods/`
  - Expected: 200 OK with saved methods
- [ ] **Delete Payment Method**: `DELETE /payments/payment-methods/{id}/delete/`
  - Expected: 200 OK with success message

### ✅ Payment with Saved Card
- [ ] **Create Second Booking**: Follow setup steps for new booking
- [ ] **Payment Intent with Saved Card**: Use `payment_method_id`
  - Expected: 201 Created with faster processing

---

## 📝 **PHASE 3: Refund System Testing**

### ✅ Refund Request Flow
- [ ] **Create Refund Request**: `POST /payments/refund-requests/`
  - Expected: 201 Created with request details
  - Save `refund_request_id`
- [ ] **List Refunds (Student)**: `GET /payments/refund-requests/`
  - Expected: 200 OK with user's refunds
- [ ] **Get Refund Details**: `GET /payments/refund-requests/{id}/`
  - Expected: 200 OK with refund details

### ✅ Admin Refund Management
- [ ] **List All Refunds (Admin)**: `GET /payments/refund-requests/` (admin token)
  - Expected: 200 OK with all refunds
- [ ] **Approve Refund**: `PATCH /payments/refund-requests/{id}/`
  - Body: `{"status": "APPROVED", "admin_notes": "Valid reason"}`
  - Expected: 200 OK with updated status
- [ ] **Process Refund**: `POST /payments/refund-requests/{id}/process/`
  - Expected: 200 OK with Stripe refund ID

### ✅ Refund Rejection (Optional)
- [ ] **Create Second Refund Request**: For testing rejection
- [ ] **Reject Refund**: `PATCH /payments/refund-requests/{id}/`
  - Body: `{"status": "REJECTED", "admin_notes": "Invalid reason"}`
  - Expected: 200 OK with rejected status

---

## 📝 **PHASE 4: Admin Dashboard Testing**

### ✅ Analytics & Reports
- [ ] **Payment Dashboard**: `GET /payments/dashboard/`
  - Expected: 200 OK with analytics data
- [ ] **Filtered Dashboard**: `GET /payments/dashboard/?date_from=2024-12-01&date_to=2024-12-31`
  - Expected: 200 OK with filtered data

---

## 📝 **PHASE 5: Error Handling Testing**

### ✅ Authentication Errors
- [ ] **No Token**: Remove Authorization header from any request
  - Expected: 401 Unauthorized
- [ ] **Invalid Token**: Use wrong token value
  - Expected: 401 Unauthorized

### ✅ Payment Errors
- [ ] **Invalid Booking ID**: `POST /payments/create-payment-intent/` with booking_id: 999
  - Expected: 400 Bad Request
- [ ] **Unconfirmed Booking**: Create booking without teacher confirmation
  - Expected: 400 Bad Request
- [ ] **Already Paid Booking**: Try to pay for same booking twice
  - Expected: 400 Bad Request
- [ ] **Other User's Payment**: Try to access another user's payment
  - Expected: 403 Forbidden

### ✅ Refund Errors
- [ ] **Invalid Payment ID**: Use non-existent payment ID
  - Expected: 400 Bad Request
- [ ] **Unpaid Booking Refund**: Try to refund unpaid booking
  - Expected: 400 Bad Request
- [ ] **Duplicate Refund**: Request refund for already refunded payment
  - Expected: 400 Bad Request
- [ ] **Excessive Amount**: Request refund more than payment amount
  - Expected: 400 Bad Request

### ✅ Authorization Errors
- [ ] **Student Access Admin**: Student tries to access `/payments/dashboard/`
  - Expected: 403 Forbidden
- [ ] **Student Process Refund**: Student tries to process refund
  - Expected: 403 Forbidden

---

## 📝 **PHASE 6: Webhook Testing**

### ✅ Webhook Events
- [ ] **Payment Success Webhook**: `POST /payments/webhooks/stripe/`
  - Use test event data from collection
  - Expected: 200 OK
- [ ] **Payment Failed Webhook**: `POST /payments/webhooks/stripe/`
  - Use test event data from collection
  - Expected: 200 OK

---

## 📝 **PHASE 7: Load & Performance Testing**

### ✅ Multiple Requests
- [ ] **Concurrent Payments**: Create multiple payment intents rapidly
- [ ] **Large Data Sets**: List payments with many records
- [ ] **Complex Queries**: Dashboard with long date ranges

---

## 🧪 **Alternative Testing: Python Script**

If you prefer automated testing, run:
```bash
python test_stripe_api.py
```

This script will:
- ✅ Test all authentication flows
- ✅ Create test data automatically
- ✅ Test payment creation and management
- ✅ Test refund system
- ✅ Test error scenarios
- ✅ Provide detailed pass/fail results

---

## 📊 **Expected Results Summary**

| Test Category | Total Tests | Expected Pass | Expected Fail |
|---------------|-------------|---------------|---------------|
| **Authentication** | 5 | 5 | 0 |
| **Payment Flow** | 8 | 6 | 2 (error tests) |
| **Saved Methods** | 6 | 6 | 0 |
| **Refund System** | 8 | 8 | 0 |
| **Admin Dashboard** | 2 | 2 | 0 |
| **Error Handling** | 12 | 0 | 12 (should fail) |
| **Webhooks** | 2 | 2 | 0 |
| **TOTAL** | **43** | **29** | **14** |

---

## 🔧 **Troubleshooting Guide**

### Common Issues:

**❌ 401 Unauthorized**
- Check Bearer token format: `Bearer your_token_here`
- Ensure token is valid and not expired
- Verify user has proper permissions

**❌ 400 Bad Request - "Booking must be confirmed"**
- Teacher must confirm booking first
- Use teacher token for confirmation

**❌ 400 Bad Request - "Already paid"**
- Create new booking for testing
- Each booking can only be paid once

**❌ 403 Forbidden**
- Check user permissions (admin vs student)
- Verify token belongs to correct user type

**❌ 500 Internal Server Error**
- Check Django server logs
- Verify database migrations applied
- Check Stripe configuration

---

## ✅ **Success Criteria**

Your testing is successful when:
- [ ] All authentication flows work
- [ ] Payment creation returns valid client_secret
- [ ] Refund workflow completes end-to-end
- [ ] Admin dashboard shows correct data
- [ ] Error scenarios fail as expected
- [ ] No unexpected 500 errors occur

---

## 📈 **Post-Testing Steps**

After successful testing:
1. **Document any issues found**
2. **Save working collection with real tokens**
3. **Set up Stripe webhook endpoints**
4. **Configure production environment**
5. **Train team on admin dashboard**

---

**🎯 Your Stripe payment system is ready for comprehensive testing!**

*Testing Guide Version: 1.0*  
*Last Updated: September 9, 2025*
