from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import UserProfile, Language

class VoiceAvatar(models.Model):
    name = models.CharField(max_length=100)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    accent = models.CharField(max_length=50)
    voice_id = models.CharField(max_length=100)  # Hume AI voice identifier
    description = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=[('male', 'Male'), ('female', 'Female')])
    age_range = models.CharField(max_length=20, choices=[
        ('child', 'Child'),
        ('young', 'Young'),
        ('adult', 'Adult'),
        ('senior', 'Senior')
    ])
    is_active = models.BooleanField(default=True)
    sample_audio_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.language.name} ({self.accent})"

class LearningContext(models.Model):
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('daily_conversation', 'Daily Conversation'),
        ('business', 'Business'),
        ('academic', 'Academic'),
        ('travel', 'Travel'),
        ('social', 'Social Interactions')
    ])
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    vocabulary = models.JSONField(default=list)  # List of key vocabulary for the context
    suggested_responses = models.JSONField(default=list)  # Common phrases/responses
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.difficulty_level})"

class AISession(models.Model):
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    voice_avatar = models.ForeignKey(VoiceAvatar, on_delete=models.CASCADE)
    context = models.ForeignKey(LearningContext, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    performance_metrics = models.JSONField(null=True)  # Store metrics from Hume AI
    
    # Session statistics
    pronunciation_score = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    fluency_score = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    vocabulary_score = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grammar_score = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.user.email} - {self.context.name} - {self.start_time}"
        
class Conversation(models.Model):
    session = models.ForeignKey(AISession, on_delete=models.CASCADE, related_name='conversations')
    timestamp = models.DateTimeField(auto_now_add=True)
    user_input = models.TextField()
    ai_response = models.TextField()
    user_audio_url = models.URLField(blank=True)
    ai_audio_url = models.URLField(blank=True)
    emotion_metrics = models.JSONField(null=True)  # Hume AI emotion analysis
    pronunciation_feedback = models.JSONField(null=True)  # Detailed pronunciation feedback
    
    def __str__(self):
        return f"Conversation in {self.session} at {self.timestamp}"

class LearningProgress(models.Model):
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    context = models.ForeignKey(LearningContext, on_delete=models.CASCADE)
    difficulty_level = models.CharField(max_length=20, choices=LearningContext.DIFFICULTY_LEVELS)
    sessions_completed = models.IntegerField(default=0)
    total_duration = models.DurationField(default=0)
    average_score = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    mastered_vocabulary = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    last_session_date = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ('student', 'context', 'difficulty_level')
        
    def __str__(self):
        return f"{self.student.user.email} - {self.context.name} Progress"
