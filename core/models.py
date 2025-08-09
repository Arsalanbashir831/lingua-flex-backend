import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    learning_goals = models.TextField(blank=True)
    proficiency_level = models.CharField(max_length=20, choices=[
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced')
    ])
    target_languages = models.JSONField(default=list)

class Teacher(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField()
    teaching_experience = models.IntegerField()  # in years
    teaching_languages = models.JSONField(default=list)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_verified = models.BooleanField(default=False)

class TeacherCertificate(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='certificates')
    name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    certificate_file = models.FileField(upload_to='certificates/')

class SupabaseUserManager(BaseUserManager):
    def create_user(self, id, email, username=None, **extra_fields):
        """
        We already get the id from Supabase, so we require it.
        Password is not used (Supabase handles auth), but AbstractBaseUser needs something,
        so set unusable password.
        """
        if not id:
            raise ValueError("Supabase user must have an id")
        if not email:
            raise ValueError("Supabase user must have an email")

        email = self.normalize_email(email)
        user = self.model(id=id, email=email, username=username or email.split("@")[0], **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Let you create a Django admin superuser manually (no Supabase id). We'll fabricate a UUID.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        supa_id = uuid.uuid4().hex
        user = self.model(id=supa_id, email=self.normalize_email(email), username=email.split("@")[0], **extra_fields)
        user.set_password(password or uuid.uuid4().hex)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        TEACHER = 'TEACHER', 'Teacher'
        ADMIN = 'ADMIN', 'Administrator'

    id = models.CharField(primary_key=True, max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = SupabaseUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.id})"

class TimeSlot(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)

class TeacherGig(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='gigs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField()  # Duration of the gig session
    is_active = models.BooleanField(default=True)

class Session(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teacher_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    zoom_link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True)

class SessionBilling(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='billing')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=100, blank=True, null=True)

class AIConversation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='ai_conversations')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='ai_conversations', null=True)
    prompt = models.TextField()
    response = models.TextField()
    audio_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sentiment_score = models.FloatField(null=True)  # For emotion analysis
    feedback = models.TextField(blank=True)  # Teacher's feedback on the conversation

class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="uploads/")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    storage_key = models.CharField(max_length=500, blank=True, null=True)  # Supabase Storage key for file
    chroma_collection = models.CharField(max_length=255, blank=True, null=True)  # For ChromaDB collection name/ID

    def __str__(self):
        return self.filename
