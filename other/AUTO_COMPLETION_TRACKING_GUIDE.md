# Tracking Auto-Completed Bookings

## Overview
There are several ways to track which bookings were completed automatically vs manually. Here are the best approaches:

## Option 1: Add Completion Method Field (Recommended)

### Step 1: Add Database Column
Run this in Supabase SQL Editor to add a tracking field:

```sql
-- Add completion_method column to track how booking was completed
ALTER TABLE bookings_sessionbooking 
ADD COLUMN IF NOT EXISTS completion_method VARCHAR(20) DEFAULT 'MANUAL';

-- Add index for efficient querying
CREATE INDEX IF NOT EXISTS idx_booking_completion_method 
ON bookings_sessionbooking(completion_method, status);
```

### Step 2: Update Auto-Complete Function
Replace your current function with this enhanced version:

```sql
-- Enhanced function that tracks auto-completion
CREATE OR REPLACE FUNCTION auto_complete_expired_bookings()
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    completed_count integer := 0;
    booking_ids integer[];
    result_json json;
BEGIN
    -- Get IDs of bookings to be completed
    SELECT array_agg(b.id) INTO booking_ids
    FROM bookings_sessionbooking b
    INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
    WHERE b.status = 'CONFIRMED'
    AND b.end_time <= NOW()
    AND p.status = 'COMPLETED';
    
    -- Update bookings with auto-completion tracking
    UPDATE bookings_sessionbooking 
    SET 
        status = 'COMPLETED',
        completion_method = 'AUTO',
        updated_at = NOW()
    WHERE id = ANY(booking_ids);
    
    -- Get count of completed bookings
    GET DIAGNOSTICS completed_count = ROW_COUNT;
    
    -- Fix missing paid_at timestamps
    UPDATE stripe_payments_payment 
    SET 
        paid_at = NOW(),
        updated_at = NOW()
    WHERE status = 'COMPLETED' 
    AND paid_at IS NULL
    AND session_booking_id = ANY(booking_ids);
    
    -- Log the operation with details
    INSERT INTO public.system_logs (
        operation, 
        details, 
        created_at
    ) VALUES (
        'auto_complete_bookings',
        jsonb_build_object(
            'completed_count', completed_count,
            'booking_ids', booking_ids,
            'timestamp', NOW()
        )::text,
        NOW()
    );
    
    -- Return detailed result
    result_json := json_build_object(
        'success', true,
        'completed_count', completed_count,
        'booking_ids', booking_ids,
        'timestamp', NOW()
    );
    
    RETURN result_json;
END;
$$;
```

### Step 3: Update Manual Completion (Django)
In your Django booking completion endpoint, set the completion method:

```python
# In bookings/views.py or views_enhanced.py - update your complete endpoint
def complete(self, request, *args, **kwargs):
    booking = self.get_object()
    
    # Your existing validation logic...
    
    # When completing manually, set completion_method
    booking.status = 'COMPLETED'
    booking.completion_method = 'MANUAL'  # Add this line
    booking.save(update_fields=['status', 'completion_method', 'updated_at'])
    
    # Rest of your logic...
```

## Option 2: Enhanced System Logs (Alternative)

If you don't want to modify the booking table, use detailed logging:

```sql
-- Enhanced logging function
CREATE OR REPLACE FUNCTION auto_complete_expired_bookings()
RETURNS json
LANGUAGE plpgsql
AS $$
DECLARE
    completed_count integer := 0;
    booking_record record;
    booking_details jsonb := '[]'::jsonb;
    result_json json;
BEGIN
    -- Loop through each booking to be completed
    FOR booking_record IN 
        SELECT b.id, b.student_id, b.teacher_id, b.end_time, p.amount_cents
        FROM bookings_sessionbooking b
        INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
        WHERE b.status = 'CONFIRMED'
        AND b.end_time <= NOW()
        AND p.status = 'COMPLETED'
    LOOP
        -- Update the booking
        UPDATE bookings_sessionbooking 
        SET 
            status = 'COMPLETED',
            updated_at = NOW()
        WHERE id = booking_record.id;
        
        -- Track details
        booking_details := booking_details || jsonb_build_object(
            'booking_id', booking_record.id,
            'student_id', booking_record.student_id,
            'teacher_id', booking_record.teacher_id,
            'end_time', booking_record.end_time,
            'amount_cents', booking_record.amount_cents,
            'completed_at', NOW()
        );
        
        completed_count := completed_count + 1;
    END LOOP;
    
    -- Fix missing paid_at timestamps
    UPDATE stripe_payments_payment 
    SET paid_at = NOW(), updated_at = NOW()
    WHERE status = 'COMPLETED' AND paid_at IS NULL;
    
    -- Detailed logging
    INSERT INTO public.system_logs (
        operation, 
        details, 
        created_at
    ) VALUES (
        'auto_complete_bookings',
        booking_details::text,
        NOW()
    );
    
    result_json := json_build_object(
        'success', true,
        'completed_count', completed_count,
        'bookings', booking_details,
        'timestamp', NOW()
    );
    
    RETURN result_json;
END;
$$;
```

## Querying Auto-Completed Bookings

### Option 1 Queries (with completion_method field):

```sql
-- See all auto-completed bookings
SELECT id, status, completion_method, updated_at
FROM bookings_sessionbooking 
WHERE completion_method = 'AUTO'
ORDER BY updated_at DESC;

-- Compare auto vs manual completions
SELECT 
    completion_method,
    COUNT(*) as booking_count,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/3600) as avg_hours_to_complete
FROM bookings_sessionbooking 
WHERE status = 'COMPLETED'
GROUP BY completion_method;

-- Recent auto-completions with details
SELECT 
    b.id,
    b.completion_method,
    b.updated_at as completed_at,
    u1.email as student_email,
    u2.email as teacher_email,
    p.amount_cents/100.0 as amount_dollars
FROM bookings_sessionbooking b
JOIN core_user u1 ON b.student_id = u1.id
JOIN core_user u2 ON b.teacher_id = u2.id  
JOIN stripe_payments_payment p ON b.id = p.session_booking_id
WHERE b.completion_method = 'AUTO'
ORDER BY b.updated_at DESC
LIMIT 10;
```

### Option 2 Queries (using system_logs):

```sql
-- See detailed auto-completion logs
SELECT 
    created_at,
    details::jsonb as completion_details
FROM system_logs 
WHERE operation = 'auto_complete_bookings'
ORDER BY created_at DESC
LIMIT 10;

-- Extract specific booking IDs from logs
SELECT 
    created_at,
    jsonb_array_elements(details::jsonb->'booking_ids') as booking_id
FROM system_logs 
WHERE operation = 'auto_complete_bookings'
ORDER BY created_at DESC;
```

## Django Admin Integration

Add this to your Django admin for easy tracking:

```python
# In bookings/admin.py
@admin.register(SessionBooking)
class SessionBookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'student', 'teacher', 'status', 
        'completion_method', 'end_time', 'updated_at'
    ]
    list_filter = [
        'status', 'completion_method', 'updated_at'
    ]
    search_fields = ['student__email', 'teacher__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student', 'teacher'
        )
```

## Monitoring Dashboard Query

Create a summary query for admin dashboard:

```sql
-- Auto-completion summary for last 7 days
SELECT 
    DATE(created_at) as completion_date,
    COUNT(*) as total_auto_completions,
    COUNT(DISTINCT details::jsonb->>'booking_ids') as unique_bookings
FROM system_logs 
WHERE operation = 'auto_complete_bookings'
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY completion_date DESC;
```

## Recommendation

Use **Option 1** (completion_method field) as it's:
- ✅ More efficient for queries
- ✅ Easier to filter and analyze
- ✅ Better for reporting
- ✅ Cleaner database design

The completion_method field will help you track exactly which bookings were completed automatically vs manually, making it easy to monitor your automation system's performance.