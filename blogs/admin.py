from django.contrib import admin
from django.utils.html import format_html
from rag_app.admin_site import admin_site
from .models import Blog, BlogCategory, BlogView


class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'blog_count', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def blog_count(self, obj):
        return obj.blogs.count()
    blog_count.short_description = 'Number of Blogs'


class BlogAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author_name', 'category', 'status', 'view_count', 
        'read_time', 'published_at', 'created_at'
    ]
    list_filter = ['status', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'content', 'author__user_profile__user__email']
    readonly_fields = ['slug', 'read_time', 'view_count', 'created_at', 'updated_at', 'published_at']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'content', 'thumbnail')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Publication', {
            'fields': ('status', 'author')
        }),
        ('SEO & Metadata', {
            'fields': ('meta_description', 'read_time', 'view_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    def author_name(self, obj):
        return obj.author_name
    author_name.short_description = 'Author'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new blog
            # Set author if not set (for admin-created blogs)
            if not obj.author:
                try:
                    from accounts.models import TeacherProfile
                    teacher_profile = TeacherProfile.objects.filter(
                        user_profile__user=request.user
                    ).first()
                    if teacher_profile:
                        obj.author = teacher_profile
                except:
                    pass
        super().save_model(request, obj, form, change)


class BlogViewAdmin(admin.ModelAdmin):
    list_display = ['blog_title', 'viewer_ip', 'viewed_at']
    list_filter = ['viewed_at', 'blog__category']
    search_fields = ['blog__title', 'viewer_ip']
    readonly_fields = ['blog', 'viewer_ip', 'user_agent', 'viewed_at']
    date_hierarchy = 'viewed_at'
    
    def blog_title(self, obj):
        return obj.blog.title
    blog_title.short_description = 'Blog Title'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of views
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing views


# Register models with custom admin site
admin_site.register(BlogCategory, BlogCategoryAdmin)
admin_site.register(Blog, BlogAdmin)
admin_site.register(BlogView, BlogViewAdmin)
