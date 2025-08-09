from django.contrib import admin
from .models import TeacherAvailability, SessionBooking, SessionFeedback

@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'day_of_week', 'start_time', 'end_time', 'is_recurring', 'date')
    list_filter = ('day_of_week', 'is_recurring')
    search_fields = ('teacher__email', 'teacher__first_name', 'teacher__last_name')

@admin.register(SessionBooking)
class SessionBookingAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'start_time', 'end_time', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('student__email', 'teacher__email', 'notes')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'is_from_student', 'created_at')
    list_filter = ('rating', 'is_from_student')
    search_fields = ('comment', 'booking__student__email', 'booking__teacher__email')
