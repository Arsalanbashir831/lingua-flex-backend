# Migration Guide: Switching to Simplified Registration

## Overview
This guide helps you migrate from the complex registration system to the simplified one.

## Changes Made

### 1. New Files Created
- `accounts/serializers_new.py` - Simplified serializers
- `accounts/views_new.py` - New view classes with simplified registration
- `accounts/urls_new.py` - Updated URL patterns
- `bookings/zoom_service.py` - Zoom API integration service
- `bookings/views_enhanced.py` - Enhanced booking views with Zoom integration
- `bookings/serializers_enhanced.py` - Enhanced booking serializers
- `bookings/urls_enhanced.py` - Enhanced booking URL patterns
- `API_Documentation_Simplified.md` - Complete API documentation
- `Zoom_Booking_API_Documentation.md` - Zoom booking system documentation
- `test_simplified_registration.py` - Test script and examples

### 2. Key Improvements
- **Simplified Registration**: Only requires email, password, full_name, and role
- **Role-based Profile Updates**: Separate endpoints for student and teacher profile updates
- **Zoom Meeting Integration**: Automatic Zoom meeting creation when teachers confirm bookings
- **Smart Availability System**: Students can check teacher availability and book specific time slots
- **Enhanced Booking Management**: Reschedule, cancel, and manage bookings with Zoom integration
- **Better Organization**: Clear separation between basic profile and role-specific data
- **Comprehensive Documentation**: Detailed API docs with examples

## Do I Need to Run Migrations?

**Answer: Probably not for the simplified registration system, but YES for the Zoom booking system.**

### For Simplified Registration System:
The simplified registration system uses the **existing database models** without any changes. You don't need new migrations because:
- User and UserProfile models already exist
- TeacherProfile model already exists
- No new fields were added

### For Zoom Booking System:
The booking models **already have Zoom fields** in your existing models:
```python
# These fields already exist in SessionBooking model
zoom_meeting_id = models.CharField(max_length=200, blank=True, null=True)
zoom_join_url = models.URLField(blank=True, null=True)
```

**Check your migration status:**
```bash
python manage.py showmigrations
```

**If you see unmigrated bookings migrations, run:**
```bash
python manage.py migrate
```

### New Features Added:
1. **Enhanced Booking System** (`bookings/` app)
   - Zoom integration service
   - Enhanced views with slot availability
   - Better serializers with Zoom info

2. **Simplified Registration** (`accounts/` app)
   - Basic registration with just essential fields
   - Role-based profile updates

## How to Switch to the New System

### Step 1: Update URL Configuration
Replace the accounts and bookings URL imports in `rag_app/urls.py`:

```python
# Change these lines:
path('api/accounts/', include('accounts.urls')),
path('api/bookings/', include('bookings.urls')),

# To these:
path('api/accounts/', include('accounts.urls_new')),
path('api/bookings/', include('bookings.urls_enhanced')),
```

### Step 1.5: Configure Zoom API (Required for booking system)
Add these to your `.env` file:
```
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret
```

Get these credentials from [Zoom Marketplace](https://marketplace.zoom.us/) by creating a JWT app.

### Step 2: Test the New System
1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. Run the test script:
   ```bash
   python test_simplified_registration.py
   ```

3. Test registration manually:
   ```bash
   curl -X POST http://localhost:8000/api/accounts/register/ \
   -H "Content-Type: application/json" \
   -d '{
     "email": "test@example.com",
     "password": "securepass123",
     "full_name": "Test User",
     "role": "student"
   }'
   ```

### Step 3: Update Frontend Application
If you have a frontend application, update it to use the new endpoints:

1. **Registration**: Use the simplified registration endpoint
2. **Profile Updates**: Use role-specific update endpoints
3. **Authentication**: Continue using Supabase authentication

## New API Endpoints Summary

### Registration
- `POST /api/accounts/register/` - Simplified registration

### Profile Management
- `GET /api/accounts/profile/me/` - Get user profile
- `PUT/PATCH /api/accounts/profile/update-student/` - Update student profile
- `GET /api/accounts/teacher/me/` - Get teacher profile
- `PUT/PATCH /api/accounts/teacher/update/` - Update teacher profile
- `GET /api/accounts/teacher/list/` - List all teachers

### Other Endpoints (Unchanged)
- Chat and messaging endpoints remain the same
- Language endpoints remain the same
- Gig management remains the same

## Benefits of the New System

1. **Faster Registration**: Users can sign up quickly with minimal information
2. **Better UX**: Progressive profile completion based on user role
3. **Cleaner Code**: Separation of concerns between registration and profile management
4. **Easier Testing**: Simple registration makes testing much easier
5. **Flexible Updates**: Users can update profiles incrementally

## Backward Compatibility

The old registration system is preserved in the original files:
- `accounts/views.py` - Original complex registration
- `accounts/serializers.py` - Original serializers
- `accounts/urls.py` - Original URL patterns

You can always revert by changing the URL import back to `accounts.urls`.

## Testing Checklist

- [ ] Registration with student role works
- [ ] Registration with teacher role works
- [ ] Student profile update works
- [ ] Teacher profile update works
- [ ] Authentication with Supabase tokens works
- [ ] Profile retrieval works for both roles
- [ ] Teacher listing works (public endpoint)

## Support

Refer to `API_Documentation_Simplified.md` for complete API documentation with examples for all endpoints.
