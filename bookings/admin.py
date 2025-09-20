from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from rag_app.admin_site import admin_site
from .models import TeacherAvailability, SessionBooking, SessionFeedback


@admin.register(TeacherAvailability)
class TeacherAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'day_of_week', 'time_slot', 'is_recurring', 'date', 'availability_status')
    list_filter = ('day_of_week', 'is_recurring', 'date')
    search_fields = ('teacher__email', 'teacher__first_name', 'teacher__last_name')
    date_hierarchy = 'date'
    
    def teacher_name(self, obj):
        return obj.teacher.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__first_name'
    
    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time Slot'
    
    def availability_status(self, obj):
        if obj.date and obj.date < timezone.now().date():
            return format_html('<span style="color: #888;">Past</span>')
        elif obj.is_recurring:
            return format_html('<span style="color: #28a745;">Recurring</span>')
        else:
            return format_html('<span style="color: #007bff;">One-time</span>')
    availability_status.short_description = 'Status'


@admin.register(SessionBooking)
class SessionBookingAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'teacher_name', 'session_date', 'time_slot', 'status', 'duration', 'booking_actions')
    list_filter = ('status', 'start_time', 'created_at')
    search_fields = ('student__email', 'teacher__email', 'notes')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Session Details', {
            'fields': ('student', 'teacher', 'start_time', 'end_time', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Tracking', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__first_name'
    
    def teacher_name(self, obj):
        return obj.teacher.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__first_name'
    
    def session_date(self, obj):
        return obj.start_time.strftime('%Y-%m-%d')
    session_date.short_description = 'Date'
    session_date.admin_order_field = 'start_time'
    
    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time'
    
    def duration(self, obj):
        return f"{obj.duration_hours:.1f}h"
    duration.short_description = 'Duration'
    
    def booking_actions(self, obj):
        now = timezone.now()
        if obj.status == 'SCHEDULED' and obj.start_time > now:
            return format_html(
                '<a href="/admin/bookings/sessionbooking/{}/change/" style="color: #007bff;">Edit</a>',
                obj.id
            )
        elif obj.status == 'COMPLETED':
            return format_html('<span style="color: #28a745;">✓ Completed</span>')
        elif obj.status == 'CANCELLED':
            return format_html('<span style="color: #dc3545;">✗ Cancelled</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ In Progress</span>')
    booking_actions.short_description = 'Actions'
    
    actions = ['mark_completed', 'mark_cancelled', 'mark_in_progress']
    
    def mark_completed(self, request, queryset):
        queryset.update(status='COMPLETED')
        self.message_user(request, f"Successfully marked {queryset.count()} sessions as completed.")
    mark_completed.short_description = "Mark as completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='CANCELLED')
        self.message_user(request, f"Successfully marked {queryset.count()} sessions as cancelled.")
    mark_cancelled.short_description = "Mark as cancelled"
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"Successfully marked {queryset.count()} sessions as in progress.")
    mark_in_progress.short_description = "Mark as in progress"


@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ('session_info', 'rating_display', 'is_from_student', 'comment_preview', 'created_at')
    list_filter = ('rating', 'is_from_student', 'created_at')
    search_fields = ('comment', 'booking__student__email', 'booking__teacher__email')
    date_hierarchy = 'created_at'
    
    def session_info(self, obj):
        return f"{obj.booking.student.get_full_name()} → {obj.booking.teacher.get_full_name()}"
    session_info.short_description = 'Session'
    
    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = '#28a745' if obj.rating >= 4 else '#ffc107' if obj.rating >= 3 else '#dc3545'
        return format_html(
            '<span style="color: {};">{} ({})</span>',
            color, stars, obj.rating
        )
    rating_display.short_description = 'Rating'
    rating_display.admin_order_field = 'rating'
    
    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:100] + "..." if len(obj.comment) > 100 else obj.comment
        return "No comment"
    comment_preview.short_description = 'Comment'


# Register all models with the custom admin site
admin_site.register(TeacherAvailability, TeacherAvailabilityAdmin)
admin_site.register(SessionBooking, SessionBookingAdmin)
admin_site.register(SessionFeedback, SessionFeedbackAdmin)
