from django.db import models
from django.utils import timezone
from accounts.models import TeacherProfile


class Campaign(models.Model):
    """
    Model to store email campaigns created by teachers
    """
    
    class StatusChoices(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENDING = 'sending', 'Sending'
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
    
    # Campaign Details
    title = models.CharField(max_length=200, help_text="Campaign title for reference")
    subject = models.CharField(max_length=255, help_text="Email subject line")
    content = models.TextField(help_text="Full custom email message content")
    
    # Teacher Information
    teacher = models.ForeignKey(
        TeacherProfile, 
        on_delete=models.CASCADE, 
        related_name='campaigns',
        help_text="Teacher who created this campaign"
    )
    
    # Campaign Status and Tracking
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.DRAFT,
        help_text="Current status of the campaign"
    )
    
    # Recipient Information
    total_recipients = models.PositiveIntegerField(
        default=0,
        help_text="Total number of students this campaign was sent to"
    )
    
    # Email Content Options
    from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Sender name (defaults to teacher's name)"
    )
    
    from_email = models.EmailField(
        blank=True,
        help_text="Sender email (defaults to teacher's email)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the campaign was actually sent"
    )
    
    # Additional Fields
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this campaign"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email Campaign"
        verbose_name_plural = "Email Campaigns"
    
    def __str__(self):
        return f"{self.title} - {self.teacher.user_profile.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Set default from_name and from_email if not provided
        if not self.from_name:
            self.from_name = self.teacher.user_profile.user.get_full_name()
        
        if not self.from_email:
            self.from_email = self.teacher.user_profile.user.email
        
        # Set sent_at timestamp when status changes to sent
        if self.status == self.StatusChoices.SENT and not self.sent_at:
            self.sent_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_sent(self):
        """Check if campaign has been sent"""
        return self.status == self.StatusChoices.SENT
    
    @property
    def can_be_sent(self):
        """Check if campaign can be sent (is draft)"""
        return self.status == self.StatusChoices.DRAFT


class CampaignRecipient(models.Model):
    """
    Model to track individual recipients of a campaign
    """
    
    class DeliveryStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent'
        DELIVERED = 'delivered', 'Delivered'
        FAILED = 'failed', 'Failed'
    
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    
    student_email = models.EmailField(help_text="Student's email address")
    student_name = models.CharField(max_length=200, help_text="Student's full name")
    
    # Delivery tracking
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING
    )
    
    # Resend email ID (for tracking)
    resend_email_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Resend email ID for tracking"
    )
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Error information
    error_message = models.TextField(
        blank=True,
        help_text="Error message if delivery failed"
    )
    
    class Meta:
        unique_together = ['campaign', 'student_email']
        ordering = ['sent_at']
    
    def __str__(self):
        return f"{self.campaign.title} -> {self.student_email}"
