from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from rag_app.admin_site import admin_site
from .models import UserProfile, TeacherProfile, Language, Chat, Message, Gig


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_name', 'role', 'city', 'country', 'status', 'created_at')
    list_filter = ('role', 'status', 'country', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'city', 'country')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role')
        }),
        ('Profile Details', {
            'fields': ('bio', 'status')
        }),
        ('Location', {
            'fields': ('city', 'country', 'postal_code')
        }),
        ('Language Preferences', {
            'fields': ('native_language', 'learning_language')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'Name'
    user_name.admin_order_field = 'user__first_name'


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'teacher_email', 'experience_years', 'qualification_short', 'gig_count')
    list_filter = ('experience_years',)
    search_fields = ('user_profile__user__email', 'user_profile__user__first_name', 'qualification', 'about')
    
    def teacher_name(self, obj):
        return obj.user_profile.user.get_full_name()
    teacher_name.short_description = 'Teacher Name'
    teacher_name.admin_order_field = 'user_profile__user__first_name'
    
    def teacher_email(self, obj):
        return obj.user_profile.user.email
    teacher_email.short_description = 'Email'
    teacher_email.admin_order_field = 'user_profile__user__email'
    
    def qualification_short(self, obj):
        return obj.qualification[:50] + "..." if len(obj.qualification) > 50 else obj.qualification
    qualification_short.short_description = 'Qualification'
    
    def gig_count(self, obj):
        return obj.gigs.count()
    gig_count.short_description = 'Active Gigs'


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'user_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    actions = ['activate_languages', 'deactivate_languages']
    
    def user_count(self, obj):
        # This would need to be implemented based on your user-language relationships
        return "N/A"  # Placeholder
    user_count.short_description = 'Users Learning'
    
    def activate_languages(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} languages.")
    activate_languages.short_description = "Activate selected languages"
    
    def deactivate_languages(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Successfully deactivated {queryset.count()} languages.")
    deactivate_languages.short_description = "Deactivate selected languages"


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('participant1_name', 'participant2_name', 'message_count', 'created_at', 'last_message_time')
    search_fields = ('participant1__email', 'participant2__email')
    date_hierarchy = 'created_at'
    
    def participant1_name(self, obj):
        return obj.participant1.get_full_name()
    participant1_name.short_description = 'Participant 1'
    participant1_name.admin_order_field = 'participant1__first_name'
    
    def participant2_name(self, obj):
        return obj.participant2.get_full_name()
    participant2_name.short_description = 'Participant 2'
    participant2_name.admin_order_field = 'participant2__first_name'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'
    
    def last_message_time(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        return last_message.timestamp if last_message else "No messages"
    last_message_time.short_description = 'Last Message'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'chat_participants', 'content_preview', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('sender__email', 'content')
    date_hierarchy = 'timestamp'
    
    def sender_name(self, obj):
        return obj.sender.get_full_name()
    sender_name.short_description = 'Sender'
    sender_name.admin_order_field = 'sender__first_name'
    
    def chat_participants(self, obj):
        return f"{obj.chat.participant1.get_full_name()} ↔ {obj.chat.participant2.get_full_name()}"
    chat_participants.short_description = 'Chat Between'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Message'


@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('service_title', 'teacher_name', 'category', 'price_per_session', 'session_duration', 'status')
    list_filter = ('category', 'status', 'session_duration')
    search_fields = ('service_title', 'short_description', 'teacher__user_profile__user__email')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('teacher', 'category', 'service_type', 'service_title')
        }),
        ('Description', {
            'fields': ('short_description', 'full_description', 'what_you_provide_in_session')
        }),
        ('Pricing & Duration', {
            'fields': ('price_per_session', 'session_duration')
        }),
        ('Tags & Status', {
            'fields': ('tags', 'status')
        }),
    )
    
    def teacher_name(self, obj):
        return obj.teacher.user_profile.user.get_full_name()
    teacher_name.short_description = 'Teacher'
    teacher_name.admin_order_field = 'teacher__user_profile__user__first_name'
    
    def session_duration_display(self, obj):
        return f"{obj.session_duration} minutes"
    session_duration_display.short_description = 'Duration'
    
    actions = ['activate_gigs', 'suspend_gigs', 'draft_gigs']
    
    def activate_gigs(self, request, queryset):
        queryset.update(status=Gig.Status.ACTIVE)
        self.message_user(request, f"Successfully activated {queryset.count()} gigs.")
    activate_gigs.short_description = "Activate selected gigs"
    
    def suspend_gigs(self, request, queryset):
        queryset.update(status=Gig.Status.SUSPENDED)
        self.message_user(request, f"Successfully suspended {queryset.count()} gigs.")
    suspend_gigs.short_description = "Suspend selected gigs"
    
    def draft_gigs(self, request, queryset):
        queryset.update(status=Gig.Status.DRAFT)
        self.message_user(request, f"Successfully moved {queryset.count()} gigs to draft.")
    draft_gigs.short_description = "Move to draft"


# Register all models with the custom admin site
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(TeacherProfile, TeacherProfileAdmin)
admin_site.register(Language, LanguageAdmin)
admin_site.register(Chat, ChatAdmin)
admin_site.register(Message, MessageAdmin)
admin_site.register(Gig, GigAdmin)
