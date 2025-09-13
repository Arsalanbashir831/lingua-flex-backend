# Fixed Supabase Function - More Permissive Version

## Problem
Your booking isn't auto-completing because `paid_at` is `null` even though payment status is `COMPLETED`.

## Solution: Updated Function (Run in Supabase SQL Editor)

```sql
-- FIXED: Create function to auto-complete bookings (handles null paid_at)
CREATE OR REPLACE FUNCTION auto_complete_expired_bookings()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    -- Update bookings that should be auto-completed
    UPDATE bookings_sessionbooking 
    SET 
        status = 'COMPLETED',
        updated_at = NOW()
    WHERE 
        status = 'CONFIRMED'
        AND end_time <= NOW()
        AND id IN (
            SELECT b.id 
            FROM bookings_sessionbooking b
            INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
            WHERE p.status = 'COMPLETED'
            -- Removed the paid_at IS NOT NULL requirement since your data shows paid_at can be null
        );
        
    -- Also update paid_at timestamp for payments that don't have it set
    UPDATE stripe_payments_payment 
    SET 
        paid_at = NOW(),
        updated_at = NOW()
    WHERE status = 'COMPLETED' 
    AND paid_at IS NULL
    AND session_booking_id IN (
        SELECT id FROM bookings_sessionbooking 
        WHERE status = 'COMPLETED'
        AND end_time <= NOW()
    );
        
    -- Log the operation (optional)
    INSERT INTO public.system_logs (
        operation, 
        details, 
        created_at
    ) VALUES (
        'auto_complete_bookings',
        'Auto-completed expired bookings with completed payments',
        NOW()
    );
END;
$$;
```

## Test the Fixed Function

```sql
-- Test the updated function
SELECT auto_complete_expired_bookings();

-- Check the results
SELECT 
    b.id,
    b.status,
    b.end_time,
    p.status as payment_status,
    p.paid_at,
    CASE 
        WHEN b.status = 'COMPLETED' THEN '✅ SUCCESS'
        ELSE '❌ NOT COMPLETED'
    END as result
FROM bookings_sessionbooking b
INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
WHERE b.id = 11;  -- Check your specific booking
```

## Alternative: Fix the paid_at Field First

If you prefer to fix the data first, run this:

```sql
-- Fix missing paid_at timestamps for completed payments
UPDATE stripe_payments_payment 
SET 
    paid_at = updated_at,  -- Use updated_at as paid_at
    updated_at = NOW()
WHERE status = 'COMPLETED' 
AND paid_at IS NULL;

-- Then use the original function
SELECT auto_complete_expired_bookings();
```

Choose the first approach (updated function) as it's more robust and handles edge cases better.