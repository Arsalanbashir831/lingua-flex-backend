from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from core.models import User, Teacher
from .models import UserProfile, TeacherProfile

@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile and TeacherProfile when a new User is created.
    This is especially useful for OAuth/Supabase users.
    """
    if created:
        with transaction.atomic():
            # Create UserProfile for all new users
            profile, _ = UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    "role": instance.role or User.Role.STUDENT, # Default to student if role not set
                    "bio": "",
                    "city": "",
                    "country": "",
                    "postal_code": "",
                    "status": "",
                    "native_language": "",
                    "learning_language": "",
                }
            )
            
            # If the user is registered as a teacher, ensure teacher-specific records exist
            if instance.role == User.Role.TEACHER:
                TeacherProfile.objects.get_or_create(
                    user_profile=profile,
                    defaults={
                        "qualification": "",
                        "experience_years": 0,
                        "certificates": [],
                        "about": "",
                    }
                )
                
                # Also ensure the core Teacher model exists
                Teacher.objects.get_or_create(
                    user=instance,
                    defaults={
                        "bio": "",
                        "teaching_experience": 0,
                        "teaching_languages": [],
                        "hourly_rate": 25.00,
                    }
                )
