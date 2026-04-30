from django.contrib import admin
from django.utils.html import format_html
from .models import User, Teacher


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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "user_name",
        "teaching_experience",
        "hourly_rate",
        "is_verified",
        "teaching_languages_display",
    )
    list_filter = ("is_verified", "teaching_experience")
    search_fields = ("user__email", "user__first_name", "user__last_name", "bio")
    actions = ["verify_teachers", "unverify_teachers"]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def user_name(self, obj):
        return obj.user.get_full_name()

    user_name.short_description = "Name"
    user_name.admin_order_field = "user__first_name"

    def teaching_languages_display(self, obj):
        if obj.teaching_languages:
            return ", ".join(obj.teaching_languages[:3])
        return "None"

    teaching_languages_display.short_description = "Teaching Languages"

    def verify_teachers(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(
            request, f"Successfully verified {queryset.count()} teachers."
        )

    verify_teachers.short_description = "Verify selected teachers"

    def unverify_teachers(self, request, queryset):
        queryset.update(is_verified=False)
        self.message_user(
            request, f"Successfully unverified {queryset.count()} teachers."
        )

    unverify_teachers.short_description = "Unverify selected teachers"
