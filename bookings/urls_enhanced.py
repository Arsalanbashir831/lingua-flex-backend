# bookings/urls_enhanced.py
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
    path('', include(router.urls)),
    
    # Additional specific endpoints
    path('slots/available/', TeacherAvailabilityViewSet.as_view({'get': 'available_slots'}), name='available-slots'),
    path('schedule/', TeacherAvailabilityViewSet.as_view({'get': 'teacher_schedule'}), name='teacher-schedule'),
    path('bookings/my/', SessionBookingViewSet.as_view({'get': 'my_bookings'}), name='my-bookings'),
    path('bookings/<uuid:pk>/confirm/', SessionBookingViewSet.as_view({'post': 'confirm'}), name='confirm-booking'),
    path('bookings/<uuid:pk>/cancel/', SessionBookingViewSet.as_view({'post': 'cancel'}), name='cancel-booking'),
    path('bookings/<uuid:pk>/reschedule/', SessionBookingViewSet.as_view({'post': 'reschedule'}), name='reschedule-booking'),
    path('bookings/<int:pk>/create_meeting/', SessionBookingViewSet.as_view({'post': 'create_meeting'}), name='create-meeting'),
]
