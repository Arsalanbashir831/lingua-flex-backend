from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from rag_app.admin_site import admin_site
from .models import Campaign, CampaignRecipient


class CampaignAdmin(admin.ModelAdmin):
    """Admin interface for Campaign model"""
    
    list_display = [
        'title', 'teacher_name', 'status', 'total_recipients', 
        'created_at', 'sent_at'
    ]
    list_filter = ['status', 'created_at', 'sent_at']
    search_fields = ['title', 'subject', 'teacher__user_profile__user__email']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'total_recipients']
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('title', 'subject', 'content', 'notes')
        }),
        ('Teacher Information', {
            'fields': ('teacher', 'from_name', 'from_email')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'total_recipients', 'created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    def teacher_name(self, obj):
        """Display teacher name"""
        return obj.teacher.user_profile.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user_profile__user__first_name'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of sent campaigns"""
        if obj and obj.is_sent:
            return False
        return super().has_delete_permission(request, obj)


class CampaignRecipientAdmin(admin.ModelAdmin):
    """Admin interface for CampaignRecipient model"""
    
    list_display = [
        'campaign_title', 'student_name', 'student_email', 
        'status', 'sent_at', 'error_message_short'
    ]
    list_filter = ['status', 'sent_at', 'campaign__status']
    search_fields = ['student_email', 'student_name', 'campaign__title']
    readonly_fields = ['sent_at', 'delivered_at']
    
    fieldsets = (
        ('Campaign & Student', {
            'fields': ('campaign', 'student_email', 'student_name')
        }),
        ('Delivery Status', {
            'fields': ('status', 'resend_email_id', 'sent_at', 'delivered_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def campaign_title(self, obj):
        """Display campaign title"""
        return obj.campaign.title
    campaign_title.short_description = 'Campaign'
    campaign_title.admin_order_field = 'campaign__title'
    
    def error_message_short(self, obj):
        """Display shortened error message"""
        if obj.error_message:
            return obj.error_message[:50] + "..." if len(obj.error_message) > 50 else obj.error_message
        return "-"
    error_message_short.short_description = 'Error'


# Register all models with the custom admin site
admin_site.register(Campaign, CampaignAdmin)
admin_site.register(CampaignRecipient, CampaignRecipientAdmin)
