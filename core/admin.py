from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from rag_app.admin_site import admin_site
from .models import (
    User, Student, Teacher, TeacherCertificate,
    TimeSlot, TeacherGig, Session, SessionBilling,
    AIConversation, File
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'profile_picture_tag', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'created_at', 'gender')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    readonly_fields = ('id', 'created_at', 'last_login')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Authentication', {
            'fields': ('id', 'email', 'username', 'is_active', 'is_staff', 'last_login')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'gender', 'date_of_birth', 'profile_picture')
        }),
        ('Role & Permissions', {
            'fields': ('role',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'first_name'
    
    def profile_picture_tag(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.profile_picture.url
            )
        return "No Image"
    profile_picture_tag.short_description = 'Profile Picture'
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} users.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} users.")
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_name', 'proficiency_level', 'target_languages_display')
    list_filter = ('proficiency_level',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'learning_goals')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'Name'
    user_name.admin_order_field = 'user__first_name'
    
    def target_languages_display(self, obj):
        if obj.target_languages:
            return ', '.join(obj.target_languages[:3])  # Show first 3 languages
        return "None"
    target_languages_display.short_description = 'Target Languages'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_name', 'teaching_experience', 'hourly_rate', 'is_verified', 'teaching_languages_display')
    list_filter = ('is_verified', 'teaching_experience')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio')
    actions = ['verify_teachers', 'unverify_teachers']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'Name'
    user_name.admin_order_field = 'user__first_name'
    
    def teaching_languages_display(self, obj):
        if obj.teaching_languages:
            return ', '.join(obj.teaching_languages[:3])
        return "None"
    teaching_languages_display.short_description = 'Teaching Languages'
    
    def verify_teachers(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Successfully verified {queryset.count()} teachers.")
    verify_teachers.short_description = "Verify selected teachers"
    
    def unverify_teachers(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(request, f"Successfully unverified {queryset.count()} teachers.")
    unverify_teachers.short_description = "Unverify selected teachers"


@admin.register(TeacherCertificate)
class TeacherCertificateAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'name', 'issuing_organization', 'issue_date', 'certificate_link')
    list_filter = ('issuing_organization', 'issue_date')
    search_fields = ('name', 'issuing_organization', 'teacher__user__email')
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user__first_name'
    
    def certificate_link(self, obj):
        if obj.certificate_file:
            return format_html(
                '<a href="{}" target="_blank">View Certificate</a>',
                obj.certificate_file.url
            )
        return "No File"
    certificate_link.short_description = 'Certificate'


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'start_time', 'end_time', 'is_available', 'duration')
    list_filter = ('is_available', 'start_time')
    search_fields = ('teacher__user__email', 'teacher__user__first_name', 'teacher__user__last_name')
    date_hierarchy = 'start_time'
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user__first_name'
    
    def duration(self, obj):
        duration = obj.end_time - obj.start_time
        hours = duration.total_seconds() / 3600
        return f"{hours:.1f} hours"
    duration.short_description = 'Duration'


@admin.register(TeacherGig)
class TeacherGigAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'title', 'price', 'duration_display', 'is_active')
    list_filter = ('is_active', 'price')
    search_fields = ('title', 'description', 'teacher__user__email')
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user__first_name'
    
    def duration_display(self, obj):
        total_seconds = obj.duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    duration_display.short_description = 'Duration'


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'teacher_name', 'start_time', 'end_time', 'status', 'zoom_link_display')
    list_filter = ('status', 'start_time')
    search_fields = ('student__user__email', 'teacher__user__email', 'notes')
    date_hierarchy = 'start_time'
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__user__first_name'
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user__first_name'
    
    def zoom_link_display(self, obj):
        if obj.zoom_link:
            return format_html('<a href="{}" target="_blank">Join Session</a>', obj.zoom_link)
        return "No Link"
    zoom_link_display.short_description = 'Zoom Link'


@admin.register(SessionBilling)
class SessionBillingAdmin(admin.ModelAdmin):
    list_display = ('session_details', 'amount', 'currency', 'is_paid', 'payment_date', 'stripe_link')
    list_filter = ('is_paid', 'currency', 'payment_date')
    search_fields = ('stripe_payment_intent', 'session__student__user__email')
    
    def session_details(self, obj):
        return f"{obj.session.student.user.get_full_name()} - {obj.session.teacher.user.get_full_name()}"
    session_details.short_description = 'Session'
    
    def stripe_link(self, obj):
        if obj.stripe_payment_intent:
            return format_html(
                '<a href="https://dashboard.stripe.com/payments/{}" target="_blank">View in Stripe</a>',
                obj.stripe_payment_intent
            )
        return "No Payment Intent"
    stripe_link.short_description = 'Stripe'


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'session_info', 'created_at', 'sentiment_score', 'has_feedback')
    list_filter = ('created_at', 'sentiment_score')
    search_fields = ('prompt', 'response', 'feedback', 'student__user__email')
    date_hierarchy = 'created_at'
    
    def student_name(self, obj):
        return obj.student.user.get_full_name()
    student_name.short_description = 'Student'
    student_name.admin_order_field = 'student__user__first_name'
    
    def session_info(self, obj):
        if obj.session:
            return f"Session with {obj.session.teacher.user.get_full_name()}"
        return "No Session"
    session_info.short_description = 'Session'
    
    def has_feedback(self, obj):
        return bool(obj.feedback)
    has_feedback.boolean = True
    has_feedback.short_description = 'Has Feedback'


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user_name', 'uploaded_at', 'file_size', 'storage_key_display')
    list_filter = ('uploaded_at',)
    search_fields = ('filename', 'user__email', 'storage_key')
    date_hierarchy = 'uploaded_at'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__first_name'
    
    def file_size(self, obj):
        if obj.file and hasattr(obj.file, 'size'):
            size = obj.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "Unknown"
    file_size.short_description = 'File Size'
    
    def storage_key_display(self, obj):
        if obj.storage_key:
            return obj.storage_key[:50] + "..." if len(obj.storage_key) > 50 else obj.storage_key
        return "No Key"
    storage_key_display.short_description = 'Storage Key'


# Register all models with the custom admin site
admin_site.register(User, UserAdmin)
admin_site.register(Student, StudentAdmin)
admin_site.register(Teacher, TeacherAdmin)
admin_site.register(TeacherCertificate, TeacherCertificateAdmin)
admin_site.register(TimeSlot, TimeSlotAdmin)
admin_site.register(TeacherGig, TeacherGigAdmin)
admin_site.register(Session, SessionAdmin)
admin_site.register(SessionBilling, SessionBillingAdmin)
admin_site.register(AIConversation, AIConversationAdmin)
admin_site.register(File, FileAdmin)
