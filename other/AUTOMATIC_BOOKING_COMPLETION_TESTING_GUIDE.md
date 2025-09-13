# 🤖 Automatic Booking Completion Testing Guide

## Overview
This guide explains how to test the automatic booking completion trigger that changes booking status from `CONFIRMED` to `COMPLETED` when the session end time is reached and payment is confirmed.

---

## 🎯 **What the Auto-Complete System Does**

### **Trigger Conditions**:
1. ✅ Booking status is `CONFIRMED`
2. ✅ Payment status is `PAID` 
3. ✅ Current server time > Booking end time
4. ✅ Session has ended (no ongoing activity)

### **Action Taken**:
- Changes booking status from `CONFIRMED` → `COMPLETED`
- Logs the completion for audit trail
- Updates the booking timestamp

---

## 🧪 **Testing Methods**

### **Method 1: Manual Command Testing (Recommended)**

#### Step 1: Check Current Bookings
```bash
# View current confirmed bookings
curl -X GET "{{base_url}}/api/bookings/bookings/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Step 2: Create Test Booking (if needed)
```bash
# Create a booking that ends soon for testing
curl -X POST "{{base_url}}/api/bookings/bookings/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gig_id": 1,
    "start_time": "2025-09-13T10:00:00Z",
    "end_time": "2025-09-13T10:30:00Z",
    "message": "Test booking for auto-completion"
  }'
```

#### Step 3: Make Payment (if needed)
```bash
# Process payment to set payment_status to PAID
curl -X POST "{{base_url}}/api/payments/process-booking-payment/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": YOUR_BOOKING_ID,
    "card_number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "cardholder_name": "Test User"
  }'
```

#### Step 4: Confirm Booking (Teacher)
```bash
# Teacher confirms the booking (creates Zoom meeting)
curl -X POST "{{base_url}}/api/bookings/bookings/YOUR_BOOKING_ID/confirm/" \
  -H "Authorization: Bearer TEACHER_ACCESS_TOKEN"
```

#### Step 5: Wait for End Time
Wait until the current server time is past the booking's `end_time`.

#### Step 6: Run Auto-Complete Command
```bash
# Run the management command to trigger auto-completion
python manage.py auto_complete_bookings
```

#### Step 7: Verify Results
```bash
# Check if booking status changed to COMPLETED
curl -X GET "{{base_url}}/api/bookings/bookings/YOUR_BOOKING_ID/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### **Method 2: Cron Job Testing (Production Setup)**

#### Step 1: Set Up Cron Job
Add to your server's crontab:
```bash
# Run every 5 minutes
*/5 * * * * /path/to/your/project/venv/bin/python /path/to/your/project/manage.py auto_complete_bookings

# Or run every minute for testing
* * * * * /path/to/your/project/venv/bin/python /path/to/your/project/manage.py auto_complete_bookings
```

#### Step 2: Create Test Scenarios
Create bookings with different end times to test the automation:

```bash
# Booking that ends in 2 minutes
curl -X POST "{{base_url}}/api/bookings/bookings/" \
  -d '{
    "end_time": "2025-09-13T14:32:00Z"  // 2 minutes from now
  }'

# Booking that ends in 10 minutes  
curl -X POST "{{base_url}}/api/bookings/bookings/" \
  -d '{
    "end_time": "2025-09-13T14:40:00Z"  // 10 minutes from now
  }'
```

#### Step 3: Monitor Cron Logs
```bash
# Check cron job execution logs
tail -f /var/log/cron
# or
grep auto_complete_bookings /var/log/syslog
```

---

### **Method 3: Time Manipulation Testing**

#### Create Past-Ended Booking for Immediate Testing:

```python
# In Django shell: python manage.py shell
from bookings.models import SessionBooking
from django.utils import timezone
from datetime import timedelta

# Create a booking that "ended" 5 minutes ago
booking = SessionBooking.objects.create(
    student_id="your_student_id",
    teacher_id="your_teacher_id", 
    gig_id=1,
    start_time=timezone.now() - timedelta(minutes=35),
    end_time=timezone.now() - timedelta(minutes=5),  # Ended 5 minutes ago
    status='CONFIRMED',
    payment_status='PAID'
)

print(f"Created test booking #{booking.id} that ended 5 minutes ago")
```

Then run the command:
```bash
python manage.py auto_complete_bookings
```

---

## 🔍 **Detailed Test Scenarios**

### **Scenario 1: Valid Auto-Completion**
**Setup:**
- Booking status: `CONFIRMED`
- Payment status: `PAID`
- End time: Past current server time
- Expected: Status changes to `COMPLETED`

**Test Steps:**
1. Create booking with end time 30 minutes from now
2. Process payment (`PAID` status)
3. Teacher confirms booking (`CONFIRMED` status)
4. Wait 35 minutes (or manipulate time)
5. Run: `python manage.py auto_complete_bookings`
6. Verify status changed to `COMPLETED`

### **Scenario 2: Incomplete Payment**
**Setup:**
- Booking status: `CONFIRMED`  
- Payment status: `PENDING`
- End time: Past current server time
- Expected: No change (stays `CONFIRMED`)

### **Scenario 3: Unconfirmed Booking**
**Setup:**
- Booking status: `PENDING`
- Payment status: `PAID`
- End time: Past current server time  
- Expected: No change (stays `PENDING`)

### **Scenario 4: Future Booking**
**Setup:**
- Booking status: `CONFIRMED`
- Payment status: `PAID`
- End time: Future time
- Expected: No change (stays `CONFIRMED`)

---

## 📊 **Expected Command Output**

### **Successful Auto-Completion:**
```
🤖 Auto-completing expired bookings...
📋 Found 3 confirmed bookings with paid status
⏰ Checking booking #4: ends at 2025-09-13 10:30:00+00:00
✅ Auto-completed booking #4 (Student: user@example.com)
⏰ Checking booking #7: ends at 2025-09-13 11:00:00+00:00  
⏭️  Booking #7 not yet ended (ends in 25 minutes)
✅ Successfully auto-completed 1 booking(s)
```

### **No Bookings to Complete:**
```
🤖 Auto-completing expired bookings...
📋 Found 0 confirmed bookings with paid status
ℹ️  No bookings need auto-completion at this time
```

### **Error Scenario:**
```
🤖 Auto-completing expired bookings...
📋 Found 2 confirmed bookings with paid status
❌ Error auto-completing booking #5: [Error details]
✅ Successfully auto-completed 1 booking(s)
```

---

## 🐛 **Troubleshooting Common Issues**

### **Issue 1: Command Not Found**
```
CommandError: Unknown command: 'auto_complete_bookings'
```
**Solution:** Ensure the management command file exists:
- `bookings/management/commands/auto_complete_bookings.py`
- `bookings/management/__init__.py`
- `bookings/management/commands/__init__.py`

### **Issue 2: Timezone Mismatch**
```
Booking appears ended but not auto-completed
```
**Solution:** Check Django timezone settings:
```python
# In Django shell
from django.utils import timezone
print(timezone.now())  # Current server time
print(timezone.get_current_timezone())  # Current timezone
```

### **Issue 3: No Bookings Found**
```
Found 0 confirmed bookings with paid status
```
**Solution:** Verify test data:
```sql
SELECT id, status, payment_status, end_time 
FROM bookings_sessionbooking 
WHERE status = 'CONFIRMED' AND payment_status = 'PAID';
```

### **Issue 4: Permission Errors**
```
Permission denied when running command
```
**Solution:** 
- Ensure proper file permissions
- Run with correct Python environment
- Check database connection permissions

---

## ⏰ **Production Cron Setup**

### **Recommended Cron Schedule:**
```bash
# Add to crontab with: crontab -e

# Run every 5 minutes (recommended for production)
*/5 * * * * /path/to/venv/bin/python /path/to/project/manage.py auto_complete_bookings >> /var/log/auto_complete_bookings.log 2>&1

# Run every minute (for testing only)
* * * * * /path/to/venv/bin/python /path/to/project/manage.py auto_complete_bookings >> /var/log/auto_complete_bookings.log 2>&1
```

### **Log Monitoring:**
```bash
# Watch real-time logs
tail -f /var/log/auto_complete_bookings.log

# Check recent completions
grep "Auto-completed" /var/log/auto_complete_bookings.log | tail -10
```

---

## 📋 **Test Checklist**

### **Before Testing:**
- [ ] Booking model has correct status and payment_status fields
- [ ] Management command file exists and is executable  
- [ ] Django timezone settings are configured (USE_TZ = True)
- [ ] Test database has sample bookings

### **During Testing:**
- [ ] Verify current server time vs booking end_time
- [ ] Check booking status before running command
- [ ] Run command and capture output
- [ ] Verify booking status after running command
- [ ] Check Django admin for updated bookings

### **After Testing:**
- [ ] Confirm only appropriate bookings were completed
- [ ] Verify no unexpected side effects
- [ ] Check application logs for errors
- [ ] Test with different timezone scenarios

---

## 🎯 **Success Criteria**

### **The automatic trigger is working correctly if:**
✅ Bookings with status `CONFIRMED` + payment status `PAID` + past end time → become `COMPLETED`
✅ Bookings that don't meet all criteria remain unchanged
✅ Command runs without errors
✅ Appropriate logging is generated
✅ No side effects on other bookings
✅ Database integrity maintained

---

**Follow this guide step-by-step to thoroughly test your automatic booking completion system!** 🚀