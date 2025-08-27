from django.contrib import admin
from django.utils.html import format_html
from rag_app.admin_site import admin_site
from .models import Gig, GigReview


class GigAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher_email', 'category', 'rate_per_hour', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at', 'languages']
    search_fields = ['title', 'teacher__user_profile__user__email', 'description']
    filter_horizontal = ['languages']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def teacher_email(self, obj):
        return obj.teacher.user_profile.user.email
    teacher_email.short_description = 'Teacher Email'
    

class GigReviewAdmin(admin.ModelAdmin):
    list_display = ['gig_title', 'user_email', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['gig__title', 'user__user__email', 'comment']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def gig_title(self, obj):
        return obj.gig.title
    gig_title.short_description = 'Gig Title'
    
    def user_email(self, obj):
        return obj.user.user.email
    user_email.short_description = 'User Email'


# Register models with custom admin site
admin_site.register(Gig, GigAdmin)
admin_site.register(GigReview, GigReviewAdmin)
