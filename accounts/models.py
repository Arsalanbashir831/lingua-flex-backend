import uuid
from django.db import models
from core.models import User
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=User.Role.choices)
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    native_language = models.CharField(max_length=50, blank=True, null=True)
    learning_language = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.role}"

class TeacherProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    qualification = models.TextField()
    experience_years = models.PositiveIntegerField()
    certificates = models.JSONField(default=list)  # Store certificate URLs
    about = models.TextField()
    
    def __str__(self):
        return f"Teacher: {self.user_profile.user.email}"

class Language(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant1 = models.ForeignKey(User, related_name='chats_as_participant1', on_delete=models.CASCADE, db_column='participant1')
    participant2 = models.ForeignKey(User, related_name='chats_as_participant2', on_delete=models.CASCADE, db_column='participant2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participant1', 'participant2')
        db_table = 'chats'  # Explicitly set table name to match Supabase

    def __str__(self):
        return f"Chat between {self.participant1.email} and {self.participant2.email}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_id = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE, db_column='chat_id')
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='sender_id')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'  # Explicitly set table name to match Supabase

    def __str__(self):
        return f"Message from {self.sender_id.email} at {self.timestamp}"

class Gig(models.Model):
    class Category(models.TextChoices):
        LANGUAGE_CONSULTATION = 'language', 'Language Consultation'
        ASTROLOGICAL_CONSULTATION = 'astrological', 'Astrological Consultation'
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        DRAFT = 'draft', 'Draft'
        SUSPENDED = 'suspended', 'Suspended'

    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='gigs')
    category = models.CharField(max_length=20, choices=Category.choices)
    service_type = models.CharField(max_length=100)
    service_title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    price_per_session = models.DecimalField(max_digits=8, decimal_places=2)
    session_duration = models.PositiveIntegerField(help_text='Duration in minutes')
    tags = models.JSONField(default=list, blank=True)
    what_you_provide_in_session = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'category')

    def __str__(self):
        return f"{self.get_category_display()} gig for {self.teacher.user_profile.user.email} - {self.get_status_display()}"

class VoiceConversation(models.Model):
    """Model to store OpenAI speech-to-speech voice conversation details"""
    
    class ConversationType(models.TextChoices):
        LANGUAGE = 'language', 'Language Consultation'
        ASTROLOGICAL = 'astrological', 'Astrological Consultation'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_conversations')
    topic = models.CharField(max_length=200, help_text='Main topic or theme of the conversation')
    transcription = models.JSONField(default=dict, help_text='JSON object containing conversation transcription data')
    native_language = models.CharField(max_length=50, help_text='User\'s native language')
    target_language = models.CharField(max_length=50, help_text='Language being learned/practiced')
    conversation_type = models.CharField(max_length=20, choices=ConversationType.choices, default=ConversationType.LANGUAGE)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text='Conversation duration in minutes')
    ai_feedback = models.JSONField(default=dict, blank=True, help_text='AI-generated feedback and analysis')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['target_language', '-created_at']),
            models.Index(fields=['conversation_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.topic} ({self.target_language}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
