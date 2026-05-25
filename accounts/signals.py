from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from core.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Safety-net: Ensure a UserProfile exists whenever a new User is created.

    The primary profile creation path is SyncSupabaseUserView + SetUserRoleView.
    This signal handles edge cases like admin panel user creation or management
    commands that bypass the API layer.

    Note: We do NOT auto-create TeacherProfile here because:
    1. User.role is now nullable (set post-signup for Google/One-Tap users)
    2. TeacherProfile creation is handled explicitly in SetUserRoleView
    """
    if created and (instance.is_staff or (getattr(instance, 'is_superuser', False))):
        with transaction.atomic():
            UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    "bio": "",
                    "city": "",
                    "country": "",
                    "postal_code": "",
                    "status": "",
                    "native_language": "",
                    "learning_language": "",
                },
            )
