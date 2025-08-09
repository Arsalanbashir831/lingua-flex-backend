from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import User

class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True)
    date = models.DateField(null=True, blank=True)  # For non-recurring availabilities

    class Meta:
        verbose_name_plural = 'Teacher availabilities'
        unique_together = ['teacher', 'day_of_week', 'start_time', 'end_time', 'date']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time')
        if not self.is_recurring and not self.date:
            raise ValidationError('Date is required for non-recurring availability')

class SessionBooking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_sessions')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    zoom_meeting_id = models.CharField(max_length=500, blank=True, null=True)  # Increased length for Zoom URLs
    zoom_join_url = models.URLField(max_length=500, blank=True, null=True)   # Increased length 
    zoom_start_url = models.URLField(max_length=500, blank=True, null=True)  # For teacher/host - increased length
    zoom_password = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time')
        if self.start_time < timezone.now():
            raise ValidationError('Cannot book sessions in the past')

    def cancel(self, reason):
        if self.status not in ['PENDING', 'CONFIRMED']:
            raise ValidationError('Cannot cancel a completed or already cancelled session')
        self.status = 'CANCELLED'
        self.cancellation_reason = reason
        self.save()

class SessionFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    booking = models.OneToOneField(SessionBooking, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_student = models.BooleanField()  # True if feedback is from student, False if from teacher

    class Meta:
        verbose_name_plural = 'Session feedback'
