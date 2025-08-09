from django.contrib import admin
from .models import (
    User, Student, Teacher, TeacherCertificate,
    TimeSlot, TeacherGig, Session, SessionBilling,
    AIConversation
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'proficiency_level')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('proficiency_level',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'teaching_experience', 'hourly_rate', 'is_verified')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('is_verified',)

@admin.register(TeacherCertificate)
class TeacherCertificateAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'name', 'issuing_organization', 'issue_date')
    search_fields = ('name', 'issuing_organization', 'teacher__user__email')

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('teacher__user__email',)

@admin.register(TeacherGig)
class TeacherGigAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'title', 'price', 'duration', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description', 'teacher__user__email')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'start_time', 'end_time', 'status')
    list_filter = ('status',)
    search_fields = ('student__user__email', 'teacher__user__email', 'notes')

@admin.register(SessionBilling)
class SessionBillingAdmin(admin.ModelAdmin):
    list_display = ('session', 'amount', 'currency', 'is_paid', 'payment_date')
    list_filter = ('is_paid', 'currency')
    search_fields = ('stripe_payment_intent', 'session__student__user__email')

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'created_at', 'sentiment_score')
    list_filter = ('created_at',)
    search_fields = ('prompt', 'response', 'feedback', 'student__user__email')
