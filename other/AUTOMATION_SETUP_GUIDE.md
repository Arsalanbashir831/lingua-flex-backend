# Automatic Booking Completion Setup Guide

## Current Status
The `auto_complete_bookings` management command exists but runs ONLY when manually executed.

## Setup Options for Automatic Execution

### Option 1: Windows Task Scheduler (Recommended)

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**
   - Click "Create Basic Task" in the right panel
   - Name: "LinguaFlex Auto Complete Bookings"
   - Description: "Automatically complete bookings when sessions end"

3. **Set Trigger**
   - Choose "Daily"
   - Set start date and time
   - Recur every: 1 day
   - Click "Advanced settings" and check "Repeat task every: 5 minutes"
   - Duration: "Indefinitely"

4. **Set Action**
   - Choose "Start a program"
   - Program: `python`
   - Arguments: `manage.py auto_complete_bookings`
   - Start in: `C:\Users\DELL\Desktop\LingualFlex_7`

5. **Test the Setup**
   - Right-click the task → "Run"
   - Check the task history for success/failure

### Option 2: Django Background Task (Code-based)

Install django-background-tasks:
```bash
pip install django-background-tasks
```

Add to settings.py:
```python
INSTALLED_APPS = [
    # ... other apps
    'background_task',
]
```

Create a background task:
```python
# In bookings/tasks.py
from background_task import background
from django.core.management import call_command

@background(schedule=300)  # Run every 5 minutes (300 seconds)
def auto_complete_bookings_task():
    call_command('auto_complete_bookings')

# To start the task (run once):
auto_complete_bookings_task(repeat=300)  # Repeat every 5 minutes
```

### Option 3: Celery (Production-Ready)

For production environments, use Celery with Redis/RabbitMQ:

```bash
pip install celery redis
```

Create periodic task in settings:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'auto-complete-bookings': {
        'task': 'bookings.tasks.auto_complete_bookings',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
```

## Testing Your Setup

### 1. Test Manual Execution First
```bash
# Run with verbose output
python manage.py auto_complete_bookings --verbose

# Test without making changes
python manage.py auto_complete_bookings --dry-run --verbose
```

### 2. Create Test Bookings
- Create bookings with end_time in the past
- Ensure payments are completed
- Run the command to see if they get auto-completed

### 3. Monitor Logs
Check Django logs and Windows Event Viewer (if using Task Scheduler) for execution status.

## Production Considerations

1. **Frequency**: Run every 1-5 minutes for responsive completion
2. **Error Handling**: Monitor logs for failures
3. **Database Load**: The query is optimized, but monitor during peak times
4. **Timezone Issues**: Ensure server timezone matches booking timezones

## Quick Start for Testing

1. **Immediate Test**:
   ```bash
   python manage.py auto_complete_bookings --dry-run --verbose
   ```

2. **Set Up Windows Task** (5-minute intervals):
   - Follow Option 1 above
   - Test by running the task manually first

3. **Monitor Results**:
   - Check booking statuses in Django admin
   - Review payment completion status
   - Monitor server logs

## Troubleshooting

- **Task not running**: Check Task Scheduler history
- **No bookings completed**: Verify booking/payment status requirements
- **Permission errors**: Ensure task runs with proper user permissions
- **Database errors**: Check Django database connection settings

Choose Option 1 (Windows Task Scheduler) for immediate setup, or Option 3 (Celery) for production environments.