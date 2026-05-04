from django.contrib import admin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "is_active",
        "profile_picture_tag",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "created_at", "gender")
    search_fields = ("email", "first_name", "last_name", "username")
    readonly_fields = ("id", "created_at", "last_login")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Authentication",
            {
                "fields": (
                    "id",
                    "email",
                    "username",
                    "is_active",
                    "is_staff",
                    "last_login",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "gender",
                    "date_of_birth",
                    "profile_picture",
                )
            },
        ),
        ("Role & Permissions", {"fields": ("role",)}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    def full_name(self, obj):
        return obj.get_full_name()

    full_name.short_description = "Full Name"
    full_name.admin_order_field = "first_name"

    def profile_picture_tag(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%;" />',
                obj.profile_picture.url,
            )
        return "No Image"

    profile_picture_tag.short_description = "Profile Picture"

    actions = ["activate_users", "deactivate_users"]

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Successfully activated {queryset.count()} users.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(
            request, f"Successfully deactivated {queryset.count()} users."
        )

    deactivate_users.short_description = "Deactivate selected users"



