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
    
    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', 'Unpaid'),
        ('PENDING', 'Payment Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Payment Failed'),
        ('REFUNDED', 'Refunded')
    ]
    
    RESCHEDULE_REQUEST_STATUS_CHOICES = [
        ('NONE', 'No Reschedule Request'),
        ('PENDING', 'Reschedule Pending Confirmation'),
        ('CONFIRMED', 'Reschedule Confirmed'),
        ('DECLINED', 'Reschedule Declined')
    ]
    
    RESCHEDULE_REQUESTED_BY_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher')
    ]
    
    PREVIOUS_RESCHEDULE_STATUS_CHOICES = [
        ('NONE', 'No Previous Request'),
        ('CONFIRMED', 'Previous Request Confirmed'),
        ('DECLINED', 'Previous Request Declined')
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_sessions')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_sessions')
    gig = models.ForeignKey('accounts.Gig', on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)  # Allow null for existing data
    
    # Session timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Session duration in hours")  # Added default
    
    # Session details
    scheduled_datetime = models.DateTimeField(null=True, blank=True, help_text="When the session is scheduled")  # Allow null for existing data
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')  # Added payment status
    
    # Reschedule tracking
    reschedule_request_status = models.CharField(
        max_length=20, 
        choices=RESCHEDULE_REQUEST_STATUS_CHOICES, 
        default='NONE',
        help_text="Status of reschedule request"
    )
    reschedule_requested_by = models.CharField(
        max_length=20, 
        choices=RESCHEDULE_REQUESTED_BY_CHOICES, 
        null=True, 
        blank=True,
        help_text="Who requested the reschedule"
    )
    previous_reschedule_request_status = models.CharField(
        max_length=20,
        choices=PREVIOUS_RESCHEDULE_STATUS_CHOICES,
        default='NONE',
        help_text="Status of the previous reschedule request (for historical tracking)"
    )
    reschedule_request_start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Requested new start time for reschedule"
    )
    reschedule_request_end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Requested new end time for reschedule"
    )
    reschedule_request_reason = models.TextField(
        blank=True,
        help_text="Reason for the reschedule request"
    )
    
    # Zoom integration
    zoom_meeting_id = models.CharField(max_length=500, blank=True, null=True)  # Increased length for Zoom URLs
    zoom_join_url = models.URLField(max_length=500, blank=True, null=True)   # Increased length 
    zoom_start_url = models.URLField(max_length=500, blank=True, null=True)  # For teacher/host - increased length
    zoom_password = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    def clean(self):
        # Validate that the session is not in the past
        if self.start_time < timezone.now():
            raise ValidationError('Cannot book sessions in the past')
        
        # Validate duration consistency if all fields are present
        if self.start_time and self.end_time and self.duration_hours:
            # Calculate actual duration from start and end times
            duration_seconds = (self.end_time - self.start_time).total_seconds()
            actual_duration_hours = duration_seconds / 3600
            
            # Allow for small rounding differences (within 1 minute tolerance)
            duration_diff = abs(actual_duration_hours - float(self.duration_hours))
            if duration_diff > 0.017:  # 1 minute = 0.017 hours
                raise ValidationError(
                    f'Duration mismatch: provided duration_hours ({self.duration_hours}) doesn\'t match '
                    f'the time difference between start_time and end_time ({actual_duration_hours:.2f} hours)'
                )
        
        # Set scheduled_datetime if not provided
        if not self.scheduled_datetime:
            self.scheduled_datetime = self.start_time

    def cancel(self, reason):
        if self.status not in ['PENDING', 'CONFIRMED']:
            raise ValidationError('Cannot cancel a completed or already cancelled session')
        self.status = 'CANCELLED'
        self.cancellation_reason = reason
        self.save()
    
    @property
    def hourly_rate(self):
        """Get hourly rate from the gig"""
        if self.gig:
            return self.gig.price_per_session  # Assuming this is hourly rate
        return 0
    
    @property 
    def total_cost(self):
        """Calculate total cost for this session"""
        return float(self.hourly_rate) * float(self.duration_hours)
    
    def __str__(self):
        return f"{self.student.email} → {self.teacher.email} | {self.gig.service_title if self.gig else 'N/A'} | {self.scheduled_datetime}"

class SessionFeedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    booking = models.OneToOneField(SessionBooking, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_student = models.BooleanField()  # True if feedback is from student, False if from teacher

    class Meta:
        verbose_name_plural = 'Session feedback'
