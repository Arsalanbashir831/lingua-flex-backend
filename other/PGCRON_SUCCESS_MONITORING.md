# pg_cron Success - Monitoring Guide

## 🎉 Congratulations! Your automatic booking completion is now active!

The response `[{"schedule": 1}]` means your cron job was successfully created with ID 1.

## Verify Your Setup

### 1. Check Active Cron Jobs
```sql
-- See all scheduled jobs
SELECT * FROM cron.job;
```

### 2. Check Job Execution History
```sql
-- See recent executions (last 10)
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;
```

### 3. Test the Function Manually First
```sql
-- Test your function to make sure it works
SELECT auto_complete_expired_bookings();

-- Check what bookings would be affected
SELECT b.id, b.status, b.end_time, p.status as payment_status, p.paid_at
FROM bookings_sessionbooking b
INNER JOIN stripe_payments_payment p ON b.id = p.booking_id
WHERE b.status = 'CONFIRMED'
AND b.end_time <= NOW()
AND p.status = 'COMPLETED';
```

### 4. Monitor System Logs
```sql
-- Check your auto-completion logs
SELECT * FROM system_logs 
WHERE operation = 'auto_complete_bookings' 
ORDER BY created_at DESC 
LIMIT 10;
```

## What Happens Next

✅ **Every 5 minutes**, pg_cron will automatically:
1. Find bookings with `status = 'CONFIRMED'`
2. Where `end_time <= NOW()` (session has ended)
3. And payment `status = 'COMPLETED'` with `paid_at` timestamp
4. Change their status to `'COMPLETED'`
5. Log the operation in `system_logs`

## Troubleshooting Commands

### If you need to modify the schedule:
```sql
-- Update the schedule (change to every 2 minutes)
SELECT cron.alter_job(1, schedule => '*/2 * * * *');

-- Or change the command
SELECT cron.alter_job(1, command => 'SELECT auto_complete_expired_bookings();');
```

### If you need to stop the job:
```sql
-- Temporarily disable
SELECT cron.alter_job(1, active => false);

-- Re-enable
SELECT cron.alter_job(1, active => true);

-- Completely remove
SELECT cron.unschedule(1);
```

### Check job status:
```sql
-- See if job is active
SELECT jobid, schedule, command, active, jobname 
FROM cron.job 
WHERE jobid = 1;
```

## Testing Your Setup

### Create Test Data
1. Create a booking with `end_time` in the past
2. Ensure the payment is marked as `COMPLETED`
3. Set booking status to `CONFIRMED`
4. Wait 5 minutes and check if it gets auto-completed

### Monitor in Real-time
```sql
-- Run this every few minutes to see changes
SELECT 
    b.id,
    b.status,
    b.end_time,
    p.status as payment_status,
    CASE 
        WHEN b.end_time <= NOW() AND p.status = 'COMPLETED' THEN 'SHOULD BE COMPLETED'
        ELSE 'CONDITIONS NOT MET'
    END as expected_action
FROM bookings_sessionbooking b
INNER JOIN stripe_payments_payment p ON b.id = p.booking_id
WHERE b.status IN ('CONFIRMED', 'COMPLETED')
ORDER BY b.end_time DESC;
```

## Success Indicators

✅ **Job is running**: `cron.job_run_details` shows recent executions  
✅ **Function works**: Manual test completes successfully  
✅ **Logs appear**: `system_logs` table gets new entries every 5 minutes  
✅ **Bookings complete**: Eligible bookings change from `CONFIRMED` to `COMPLETED`  

## Performance Notes

- The function uses efficient database queries with proper indexes
- Only processes bookings that meet all criteria
- Atomic transactions prevent data inconsistency
- Minimal resource usage (runs in milliseconds)

Your automatic booking completion system is now live! 🚀