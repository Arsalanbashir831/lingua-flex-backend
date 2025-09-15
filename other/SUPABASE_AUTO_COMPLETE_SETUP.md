# Supabase Database Trigger for Auto-Completing Bookings

## Overview
Instead of running a Django management command, you can set up automatic booking completion directly in your Supabase database using PostgreSQL triggers and scheduled functions.

## Option 1: Database Trigger (Recommended)

### Step 1: Create the Auto-Complete Function

Go to your Supabase Dashboard → SQL Editor and run this SQL:

```sql
-- Create function to auto-complete bookings
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
            AND p.paid_at IS NOT NULL
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

### Step 2: Create System Logs Table (Optional)

```sql
-- Create logs table to track auto-completion runs
CREATE TABLE IF NOT EXISTS public.system_logs (
    id BIGSERIAL PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Step 3: Set Up Scheduled Execution

#### Method A: Using pg_cron (if available)

**⚠️ NOTE: Most Supabase instances don't have pg_cron enabled. Skip to Method B if you get a "schema cron does not exist" error.**

First, check if pg_cron is available:
```sql
-- Check if pg_cron extension exists
SELECT * FROM pg_available_extensions WHERE name = 'pg_cron';

-- If available, enable it (requires superuser privileges)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Then schedule the function
SELECT cron.schedule('auto-complete-bookings', '*/5 * * * *', 'SELECT auto_complete_expired_bookings();');
```

If you get an error like "schema cron does not exist", use **Method B** instead.

#### Method B: Using Supabase Edge Functions (Recommended for most users)

Since pg_cron isn't available on your Supabase instance, use this approach:

1. **Create Edge Function**:
```typescript
// supabase/functions/auto-complete-bookings/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Call the database function
    const { data, error } = await supabase.rpc('auto_complete_expired_bookings')

    if (error) {
      console.error('Error auto-completing bookings:', error)
      return new Response(
        JSON.stringify({ error: error.message }),
        { 
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        }
      )
    }

    return new Response(
      JSON.stringify({ success: true, message: 'Auto-completion completed' }),
      { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})
```

2. **Deploy the Edge Function**:
```bash
supabase functions deploy auto-complete-bookings
```

3. **Set up Cron Job** (using GitHub Actions, Vercel Cron, or similar):
```yaml
# .github/workflows/auto-complete-bookings.yml
name: Auto Complete Bookings
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
  workflow_dispatch:

jobs:
  auto-complete:
    runs-on: ubuntu-latest
    steps:
      - name: Call Supabase Function
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ANON_KEY }}" \
            -H "Content-Type: application/json" \
            "${{ secrets.SUPABASE_URL }}/functions/v1/auto-complete-bookings"
```

#### Method C: Simple HTTP Endpoint + External Cron (Easiest Alternative)

If Edge Functions are too complex, create a simple Django endpoint that calls the database function:

1. **Add to your Django `urls.py`**:
```python
# In your main urls.py or create a new app for admin tasks
from django.urls import path, include

urlpatterns = [
    # ... your existing urls
    path('admin-tasks/', include('admin_tasks.urls')),  # Create this app
]
```

2. **Create Django view**:
```python
# admin_tasks/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import connection
import json

@csrf_exempt
@require_http_methods(["POST"])
def auto_complete_bookings(request):
    try:
        # Verify API key (optional but recommended)
        api_key = request.headers.get('X-API-Key')
        if api_key != 'your-secret-api-key':  # Replace with actual key
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Call the database function
        with connection.cursor() as cursor:
            cursor.execute("SELECT auto_complete_expired_bookings()")
            
        return JsonResponse({
            'success': True, 
            'message': 'Auto-completion triggered successfully'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# admin_tasks/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('auto-complete-bookings/', views.auto_complete_bookings, name='auto_complete_bookings'),
]
```

3. **Use any external cron service**:
   - **Uptime Robot** (free): Monitor + call your endpoint every 5 minutes
   - **Cron-job.org** (free): Schedule HTTP requests
   - **GitHub Actions** (as shown in Method B)
   - **Your hosting provider's cron** (if you have server access)

Example curl command:
```bash
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  "https://your-django-app.com/admin-tasks/auto-complete-bookings/"
```

## Option 2: Database Trigger on Time-Based Events

### Create Trigger Function
```sql
-- Function that runs when booking end_time is reached
CREATE OR REPLACE FUNCTION check_booking_completion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if booking should be auto-completed
    IF NEW.end_time <= NOW() 
       AND NEW.status = 'CONFIRMED'
       AND EXISTS (
           SELECT 1 FROM stripe_payments_payment 
           WHERE session_booking_id = NEW.id 
           AND status = 'COMPLETED' 
           AND paid_at IS NOT NULL
       ) THEN
        NEW.status = 'COMPLETED';
        NEW.updated_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$;

-- Create trigger
CREATE TRIGGER booking_auto_complete_trigger
    BEFORE UPDATE ON bookings_sessionbooking
    FOR EACH ROW
    EXECUTE FUNCTION check_booking_completion();
```

## Option 3: Real-time Database Function (Advanced)

```sql
-- Create a function that can be called via REST API
CREATE OR REPLACE FUNCTION public.auto_complete_bookings_api()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    completed_count integer;
    result_json json;
BEGIN
    -- Count bookings to be completed
    SELECT COUNT(*) INTO completed_count
    FROM bookings_sessionbooking b
    INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
    WHERE b.status = 'CONFIRMED'
    AND b.end_time <= NOW()
    AND p.status = 'COMPLETED'
    AND p.paid_at IS NOT NULL;
    
    -- Update the bookings
    UPDATE bookings_sessionbooking 
    SET 
        status = 'COMPLETED',
        updated_at = NOW()
    WHERE status = 'CONFIRMED'
    AND end_time <= NOW()
    AND id IN (
        SELECT b.id 
        FROM bookings_sessionbooking b
        INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
        WHERE p.status = 'COMPLETED' 
        AND p.paid_at IS NOT NULL
    );
    
    -- Return result
    result_json := json_build_object(
        'success', true,
        'completed_count', completed_count,
        'timestamp', NOW()
    );
    
    RETURN result_json;
END;
$$;
```

Then call this from your Django app or external cron:
```python
# In Django, you can call this via raw SQL
from django.db import connection

def trigger_auto_completion():
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.auto_complete_bookings_api()")
        result = cursor.fetchone()[0]
        return result
```

## Setup Instructions

### Quick Start (Recommended):

1. **Go to Supabase Dashboard** → SQL Editor
2. **Run the auto-complete function** (from Option 1, Step 1)
3. **Set up scheduling**:
   - If pg_cron is available: Use Method A
   - Otherwise: Use Edge Functions (Method B)

### Testing:

```sql
-- Test the function manually
SELECT auto_complete_expired_bookings();

-- Check what bookings would be affected
SELECT b.id, b.status, b.end_time, p.status as payment_status
FROM bookings_sessionbooking b
INNER JOIN stripe_payments_payment p ON b.id = p.session_booking_id
WHERE b.status = 'CONFIRMED'
AND b.end_time <= NOW()
AND p.status = 'COMPLETED';
```

### Monitoring:

```sql
-- Check system logs
SELECT * FROM system_logs 
WHERE operation = 'auto_complete_bookings' 
ORDER BY created_at DESC 
LIMIT 10;
```

## Benefits of Database-Level Automation:

✅ **Faster**: No Django overhead  
✅ **More reliable**: Runs even if Django is down  
✅ **Lower resource usage**: Direct database operations  
✅ **Atomic**: All operations in single transaction  
✅ **Timezone aware**: Uses database timezone functions  

Choose **Option 1 with Edge Functions** for the most robust solution, or **Option 3** if you want to keep some control from your Django application.