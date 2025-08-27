from django.contrib import admin
from django.utils.html import format_html
from rag_app.admin_site import admin_site
from .models import VoiceAvatar, LearningContext, AISession, Conversation, LearningProgress, LearningProgress


class VoiceAvatarAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'accent', 'gender', 'age_range', 'is_active']
    list_filter = ['language', 'gender', 'age_range', 'is_active']
    search_fields = ['name', 'accent', 'description']
    
    
class LearningContextAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty_level', 'is_active']
    list_filter = ['category', 'difficulty_level', 'is_active']
    search_fields = ['name', 'description']
    

class AISessionAdmin(admin.ModelAdmin):
    list_display = ['student_email', 'voice_avatar', 'context', 'is_completed', 'start_time']
    list_filter = ['is_completed', 'start_time', 'voice_avatar__language']
    search_fields = ['student__user__email', 'voice_avatar__name']
    readonly_fields = ['start_time', 'end_time', 'duration']
    date_hierarchy = 'start_time'
    
    def student_email(self, obj):
        return obj.student.user.email
    student_email.short_description = 'Student Email'


class ConversationAdmin(admin.ModelAdmin):
    list_display = ['session_info', 'timestamp', 'user_input_short']
    list_filter = ['timestamp', 'session__voice_avatar__language']
    search_fields = ['user_input', 'ai_response', 'session__student__user__email']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def session_info(self, obj):
        return f"{obj.session.student.user.email} - {obj.session.voice_avatar.name}"
    session_info.short_description = 'Session Info'
    
    def user_input_short(self, obj):
        return obj.user_input[:50] + "..." if len(obj.user_input) > 50 else obj.user_input
    user_input_short.short_description = 'User Input'


class LearningProgressAdmin(admin.ModelAdmin):
    list_display = ['student_email', 'context', 'difficulty_level', 'sessions_completed', 'average_score']
    list_filter = ['difficulty_level', 'context', 'last_session_date']
    search_fields = ['student__user__email', 'context__name']
    readonly_fields = ['last_session_date']
    
    def student_email(self, obj):
        return obj.student.user.email
    student_email.short_description = 'Student Email'


# Register models with custom admin site
admin_site.register(VoiceAvatar, VoiceAvatarAdmin)
admin_site.register(LearningContext, LearningContextAdmin)
admin_site.register(AISession, AISessionAdmin)
admin_site.register(Conversation, ConversationAdmin)
admin_site.register(LearningProgress, LearningProgressAdmin)
