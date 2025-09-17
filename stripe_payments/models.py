# Platform-wide payment settings (singleton)
from django.db import models

class PaymentSettings(models.Model):
    platform_fee_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00,
        help_text="Platform fee percentage (e.g., 5.00 for 5%)"
    )

    class Meta:
        verbose_name = "Payment Settings"
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"Platform Fee: {self.platform_fee_percent}%"
from django.db import models
from django.utils import timezone
from decimal import Decimal
import stripe
from django.conf import settings


class Payment(models.Model):
    """
    Main payment model for session bookings
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUND_REQUESTED', 'Refund Requested'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled')
    ]
    
    # Relationships
    session_booking = models.OneToOneField(
        'bookings.SessionBooking', 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    student = models.ForeignKey(
        'core.User', 
        on_delete=models.CASCADE, 
        related_name='payments_made'
    )
    teacher = models.ForeignKey(
        'core.User', 
        on_delete=models.CASCADE, 
        related_name='payments_received'
    )
    gig = models.ForeignKey(
        'accounts.Gig', 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    # Stripe Details
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Payment Calculation
    amount_cents = models.IntegerField(help_text="Amount in cents (USD)")
    hourly_rate_cents = models.IntegerField(help_text="Teacher's hourly rate in cents")
    session_duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Session duration in hours"
    )
    platform_fee_cents = models.IntegerField(default=0, help_text="Platform fee in cents")
    
    # Status & Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method_type = models.CharField(max_length=50, blank=True)  # 'card', 'wallet', etc.
    currency = models.CharField(max_length=3, default='USD')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata for additional info
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.student.email} → {self.teacher.email} (${self.amount_dollars})"
    
    @property
    def amount_dollars(self):
        """Convert cents to dollars for display"""
        return Decimal(self.amount_cents) / 100
    
    @property
    def hourly_rate_dollars(self):
        """Convert hourly rate cents to dollars"""
        return Decimal(self.hourly_rate_cents) / 100
    
    def calculate_amount_cents(self):
        """Calculate total payment amount in cents"""
        hourly_rate = Decimal(self.hourly_rate_cents)
        duration = self.session_duration_hours
        total_cents = int(hourly_rate * duration)
        return total_cents + self.platform_fee_cents


class SavedPaymentMethod(models.Model):
    """
    Store student's saved payment methods from Stripe
    """
    student = models.ForeignKey(
        'core.User', 
        on_delete=models.CASCADE, 
        related_name='saved_payment_methods'
    )
    stripe_payment_method_id = models.CharField(max_length=255, unique=True)
    stripe_customer_id = models.CharField(max_length=255)
    
    # Card Details (for display purposes)
    card_brand = models.CharField(max_length=20)  # visa, mastercard, amex, etc.
    card_last_four = models.CharField(max_length=4)
    card_exp_month = models.IntegerField()
    card_exp_year = models.IntegerField()
    card_country = models.CharField(max_length=2, blank=True)  # Country code
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['student', 'is_active']),
        ]
    
    def __str__(self):
        default_text = " (Default)" if self.is_default else ""
        return f"{self.card_brand.title()} ****{self.card_last_four}{default_text}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per student
        if self.is_default:
            SavedPaymentMethod.objects.filter(
                student=self.student, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class RefundRequest(models.Model):
    """
    Student refund requests with admin approval workflow
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PROCESSED', 'Refund Processed')
    ]
    
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='refund_requests'
    )
    student = models.ForeignKey('core.User', on_delete=models.CASCADE)
    
    # Request Details
    reason = models.TextField(help_text="Student's reason for refund request")
    requested_amount_cents = models.IntegerField(help_text="Requested refund amount in cents")
    
    # Admin Review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_notes = models.TextField(blank=True, help_text="Admin's review notes")
    reviewed_by = models.ForeignKey(
        'core.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_refunds'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe Refund Details (when processed)
    stripe_refund_id = models.CharField(max_length=255, blank=True, null=True)
    refunded_amount_cents = models.IntegerField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['student', '-created_at']),
        ]
    
    def __str__(self):
        return f"Refund Request {self.id} - {self.student.email} (${self.requested_amount_dollars})"
    
    @property
    def requested_amount_dollars(self):
        """Convert requested amount from cents to dollars"""
        return Decimal(self.requested_amount_cents) / 100
    
    @property
    def refunded_amount_dollars(self):
        """Convert refunded amount from cents to dollars"""
        if self.refunded_amount_cents:
            return Decimal(self.refunded_amount_cents) / 100
        return None


class StripeCustomer(models.Model):
    """
    Link Django users to Stripe customers
    """
    user = models.OneToOneField(
        'core.User', 
        on_delete=models.CASCADE, 
        related_name='stripe_customer'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    
    # Customer Details
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Stripe Customer: {self.user.email} ({self.stripe_customer_id})"


class PaymentAnalytics(models.Model):
    """
    Daily payment analytics for admin dashboard
    """
    date = models.DateField(unique=True)
    
    # Daily Metrics
    total_payments_count = models.IntegerField(default=0)
    total_amount_cents = models.IntegerField(default=0)
    successful_payments_count = models.IntegerField(default=0)
    failed_payments_count = models.IntegerField(default=0)
    refund_requests_count = models.IntegerField(default=0)
    refunds_processed_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Payment Analytics"
    
    def __str__(self):
        return f"Analytics for {self.date} - ${self.total_amount_dollars}"
    
    @property
    def total_amount_dollars(self):
        """Convert total amount from cents to dollars"""
        return Decimal(self.total_amount_cents) / 100
