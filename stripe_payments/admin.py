"""
Admin interface for Stripe payment system
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from .models import (
    Payment, SavedPaymentMethod, RefundRequest, 
    StripeCustomer, PaymentAnalytics
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for payments
    """
    list_display = [
        'id', 'payment_status_badge', 'student_link', 'teacher_link',
        'amount_display', 'session_date', 'created_at'
    ]
    list_filter = [
        'status', 'currency', 'created_at', 'paid_at'
    ]
    search_fields = [
        'student__email', 'teacher__email', 'gig__title',
        'stripe_payment_intent_id', 'stripe_charge_id'
    ]
    readonly_fields = [
        'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id',
        'amount_cents', 'hourly_rate_cents', 'platform_fee_cents',
        'created_at', 'paid_at', 'updated_at'
    ]
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'status', 'amount_cents', 'hourly_rate_cents',
                'session_duration_hours', 'platform_fee_cents',
                'currency', 'payment_method_type'
            )
        }),
        ('Relationships', {
            'fields': (
                'session_booking', 'student', 'teacher', 'gig'
            )
        }),
        ('Stripe Details', {
            'fields': (
                'stripe_payment_intent_id', 'stripe_charge_id',
                'stripe_customer_id'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'paid_at', 'updated_at'
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def payment_status_badge(self, obj):
        """Display payment status with color badge"""
        color_map = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
            'FAILED': 'red',
            'REFUND_REQUESTED': 'purple',
            'REFUNDED': 'gray',
            'CANCELLED': 'black'
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    payment_status_badge.short_description = 'Status'
    
    def student_link(self, obj):
        """Link to student admin page"""
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.email)
    student_link.short_description = 'Student'
    
    def teacher_link(self, obj):
        """Link to teacher admin page"""
        url = reverse('admin:core_user_change', args=[obj.teacher.id])
        return format_html('<a href="{}">{}</a>', url, obj.teacher.email)
    teacher_link.short_description = 'Teacher'
    
    def amount_display(self, obj):
        """Display formatted amount"""
        return f"${obj.amount_dollars}"
    amount_display.short_description = 'Amount'
    
    def session_date(self, obj):
        """Display session date"""
        if obj.session_booking and obj.session_booking.scheduled_datetime:
            return obj.session_booking.scheduled_datetime.strftime('%Y-%m-%d %H:%M')
        return '-'
    session_date.short_description = 'Session Date'


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for refund requests
    """
    list_display = [
        'id', 'status_badge', 'student_link', 'requested_amount_display',
        'payment_link', 'created_at', 'reviewed_at'
    ]
    list_filter = [
        'status', 'created_at', 'reviewed_at'
    ]
    search_fields = [
        'student__email', 'payment__stripe_payment_intent_id', 'reason'
    ]
    readonly_fields = [
        'payment', 'student', 'requested_amount_cents',
        'stripe_refund_id', 'refunded_amount_cents',
        'created_at', 'refunded_at', 'updated_at'
    ]
    fieldsets = (
        ('Request Details', {
            'fields': (
                'payment', 'student', 'reason',
                'requested_amount_cents', 'status'
            )
        }),
        ('Admin Review', {
            'fields': (
                'admin_notes', 'reviewed_by', 'reviewed_at'
            )
        }),
        ('Refund Processing', {
            'fields': (
                'stripe_refund_id', 'refunded_amount_cents', 'refunded_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )
    actions = ['approve_refunds', 'reject_refunds']
    
    def status_badge(self, obj):
        """Display status with color badge"""
        color_map = {
            'PENDING': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
            'PROCESSED': 'blue'
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def student_link(self, obj):
        """Link to student admin page"""
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.email)
    student_link.short_description = 'Student'
    
    def payment_link(self, obj):
        """Link to payment admin page"""
        url = reverse('admin:stripe_payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">${}</a>', url, obj.payment.amount_dollars)
    payment_link.short_description = 'Payment'
    
    def requested_amount_display(self, obj):
        """Display formatted requested amount"""
        return f"${obj.requested_amount_dollars}"
    requested_amount_display.short_description = 'Requested Amount'
    
    def approve_refunds(self, request, queryset):
        """Bulk approve refund requests"""
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} refund requests approved.')
    approve_refunds.short_description = 'Approve selected refund requests'
    
    def reject_refunds(self, request, queryset):
        """Bulk reject refund requests"""
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} refund requests rejected.')
    reject_refunds.short_description = 'Reject selected refund requests'


@admin.register(SavedPaymentMethod)
class SavedPaymentMethodAdmin(admin.ModelAdmin):
    """
    Admin interface for saved payment methods
    """
    list_display = [
        'id', 'student_link', 'card_display', 'is_default',
        'is_active', 'created_at'
    ]
    list_filter = [
        'card_brand', 'is_default', 'is_active', 'created_at'
    ]
    search_fields = [
        'student__email', 'stripe_payment_method_id', 'card_last_four'
    ]
    readonly_fields = [
        'stripe_payment_method_id', 'stripe_customer_id',
        'card_brand', 'card_last_four', 'card_exp_month',
        'card_exp_year', 'card_country', 'created_at', 'updated_at'
    ]
    
    def student_link(self, obj):
        """Link to student admin page"""
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.email)
    student_link.short_description = 'Student'
    
    def card_display(self, obj):
        """Display card information"""
        return f"{obj.card_brand.title()} ****{obj.card_last_four}"
    card_display.short_description = 'Card'


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    """
    Admin interface for Stripe customers
    """
    list_display = [
        'id', 'user_link', 'stripe_customer_id',
        'email', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = [
        'user__email', 'stripe_customer_id', 'email', 'name'
    ]
    readonly_fields = [
        'stripe_customer_id', 'created_at', 'updated_at'
    ]
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:core_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'User'


@admin.register(PaymentAnalytics)
class PaymentAnalyticsAdmin(admin.ModelAdmin):
    """
    Admin interface for payment analytics
    """
    list_display = [
        'date', 'total_payments_count', 'total_amount_display',
        'successful_payments_count', 'failed_payments_count',
        'refund_requests_count'
    ]
    list_filter = ['date']
    readonly_fields = [
        'date', 'total_payments_count', 'total_amount_cents',
        'successful_payments_count', 'failed_payments_count',
        'refund_requests_count', 'refunds_processed_count',
        'created_at', 'updated_at'
    ]
    
    def total_amount_display(self, obj):
        """Display formatted total amount"""
        return f"${obj.total_amount_dollars}"
    total_amount_display.short_description = 'Total Amount'
    
    def has_add_permission(self, request):
        """Disable manual creation of analytics"""
        return False


# Customize admin site header
admin.site.site_header = "LinguaFlex Payment Administration"
admin.site.site_title = "LinguaFlex Payments"
admin.site.index_title = "Payment Management Dashboard"
