from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_enhanced import (
    TeacherAvailabilityViewSet,
    SessionBookingViewSet,
    SessionFeedbackViewSet
)

router = DefaultRouter()
router.register(r'availability', TeacherAvailabilityViewSet, basename='availability')
router.register(r'bookings', SessionBookingViewSet, basename='booking')
router.register(r'feedback', SessionFeedbackViewSet, basename='feedback')

urlpatterns = [
    # Custom endpoints that need to come BEFORE the router to avoid conflicts
    path('bookings/my/', SessionBookingViewSet.as_view({'get': 'my_bookings'}), name='my-bookings'),
    path('slots/available/', TeacherAvailabilityViewSet.as_view({'get': 'available_slots'}), name='available-slots'),
    path('schedule/', TeacherAvailabilityViewSet.as_view({'get': 'teacher_schedule'}), name='teacher-schedule'),
    path('availability/weekly/', TeacherAvailabilityViewSet.as_view({'get': 'weekly_availability'}), name='weekly-availability'),
    
    # Bulk availability management endpoints
    path('availability/bulk/', TeacherAvailabilityViewSet.as_view({'post': 'bulk_create'}), name='bulk-availability'),
    path('availability/bulk/update/', TeacherAvailabilityViewSet.as_view({'put': 'bulk_update', 'patch': 'bulk_update'}), name='bulk-update-availability'),
    path('availability/bulk/delete/', TeacherAvailabilityViewSet.as_view({'delete': 'bulk_delete'}), name='bulk-delete-availability'),
    path('availability/replace/', TeacherAvailabilityViewSet.as_view({'put': 'replace_weekly_schedule'}), name='replace-weekly-schedule'),
    
    # Fixed booking endpoints - using int instead of uuid since SessionBooking uses auto-increment IDs
    path('bookings/<int:pk>/confirm/', SessionBookingViewSet.as_view({'post': 'confirm'}), name='confirm-booking'),
    path('bookings/<int:pk>/complete/', SessionBookingViewSet.as_view({'post': 'complete'}), name='complete-booking'),
    path('bookings/<int:pk>/cancel/', SessionBookingViewSet.as_view({'post': 'cancel'}), name='cancel-booking'),
    path('bookings/<int:pk>/reschedule/', SessionBookingViewSet.as_view({'post': 'reschedule'}), name='reschedule-booking'),
    path('bookings/<int:pk>/create_meeting/', SessionBookingViewSet.as_view({'post': 'create_meeting'}), name='create-meeting'),
    path('bookings/<int:pk>/meeting_info/', SessionBookingViewSet.as_view({'get': 'meeting_info'}), name='meeting-info'),
    path('bookings/<int:pk>/complete_manually/', SessionBookingViewSet.as_view({'post': 'complete_manually'}), name='complete-booking-manually'),
    
    # Include router URLs LAST
    path('', include(router.urls)),
]
