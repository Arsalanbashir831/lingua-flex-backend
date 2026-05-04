from django.contrib import admin
from .models import Blog


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author_name",
        "status",
        "read_time",
        "published_at",
        "created_at",
    ]
    list_filter = ["status", "created_at", "published_at"]
    search_fields = ["title", "content", "author__user_profile__user__email"]
    readonly_fields = [
        "slug",
        "read_time",
        "created_at",
        "updated_at",
        "published_at",
    ]
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Basic Information", {"fields": ("title", "slug", "content", "thumbnail")}),
        ("Categorization", {"fields": ("tags",)}),
        ("Publication", {"fields": ("status", "author")}),
        ("SEO & Metadata", {"fields": ("meta_description", "read_time")}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "published_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def author_name(self, obj):
        return obj.author_name

    author_name.short_description = "Author"

    def save_model(self, request, obj, form, change):
        """
        Custom save_model to automatically set author for new blogs
        created via the admin panel if not specified.
        """
        if not change and not obj.author:
            # Try to find a teacher profile for the current user
            from accounts.models import TeacherProfile

            teacher_profile = TeacherProfile.objects.filter(
                user_profile__user=request.user
            ).first()
            if teacher_profile:
                obj.author = teacher_profile

        super().save_model(request, obj, form, change)



