from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherAvailabilityViewSet,
    SessionBookingViewSet,
)

router = DefaultRouter()
router.register(r"availability", TeacherAvailabilityViewSet, basename="availability")
router.register(r"bookings", SessionBookingViewSet, basename="booking")

urlpatterns = [
    # Custom endpoints that need to come BEFORE the router to avoid conflicts
    path(
        "bookings/my/",
        SessionBookingViewSet.as_view({"get": "my_bookings"}),
        name="my-bookings",
    ),
    path(
        "availability/weekly/",
        TeacherAvailabilityViewSet.as_view({"get": "weekly_availability"}),
        name="weekly-availability",
    ),
    # Bulk availability management endpoints
    path(
        "availability/bulk/",
        TeacherAvailabilityViewSet.as_view({"post": "bulk_create"}),
        name="bulk-availability",
    ),
    path(
        "availability/replace/",
        TeacherAvailabilityViewSet.as_view({"put": "replace_weekly_schedule"}),
        name="replace-weekly-schedule",
    ),
    # Fixed booking endpoints - using int instead of uuid since SessionBooking uses auto-increment IDs
    path(
        "bookings/<int:pk>/confirm/",
        SessionBookingViewSet.as_view({"post": "confirm"}),
        name="confirm-booking",
    ),
    path(
        "bookings/<int:pk>/cancel/",
        SessionBookingViewSet.as_view({"post": "cancel"}),
        name="cancel-booking",
    ),
    path(
        "bookings/<int:pk>/reschedule/",
        SessionBookingViewSet.as_view({"post": "reschedule"}),
        name="reschedule-booking",
    ),
    # Include router URLs LAST
    path("", include(router.urls)),
]
