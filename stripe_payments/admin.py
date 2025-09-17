
"""
Enhanced Admin interface for Stripe payment system with complete management capabilities
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
import csv
import json
import stripe
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

from .models import (
    Payment, SavedPaymentMethod, RefundRequest, 
    StripeCustomer, PaymentAnalytics
)
from .services import StripePaymentService


from .models import PaymentSettings
# Register PaymentSettings in admin
@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ["platform_fee_percent"]
    fields = ["platform_fee_percent"]
    def has_add_permission(self, request):
        # Only allow one settings row
        return not PaymentSettings.objects.exists()

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for payments with complete management capabilities
    """
    list_display = [
        'id', 'payment_status_badge', 'student_link', 'teacher_link',
        'amount_display', 'platform_fee_display', 'session_date', 
        'stripe_link', 'created_at', 'booking_link'
    ]
    list_filter = [
        'status', 'currency', 'created_at', 'paid_at',
        'payment_method_type', 'session_booking__status'
    ]
    search_fields = [
        'student__email', 'teacher__email', 'gig__service_title',
        'stripe_payment_intent_id', 'stripe_charge_id', 'id'
    ]
    readonly_fields = [
        'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_customer_id',
        'amount_cents', 'hourly_rate_cents', 'platform_fee_cents',
        'created_at', 'paid_at', 'updated_at', 'calculate_fees',
        'stripe_dashboard_link', 'refund_history',
        'amount_display_large', 'payment_status_badge_display', 'platform_fee_display_large'
    ]
    
    fieldsets = (
        ('Payment Overview', {
            'fields': (
                'payment_status_badge_display', 'amount_display_large', 
                'platform_fee_display_large', 'calculate_fees'
            )
        }),
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
        ('Stripe Integration', {
            'fields': (
                'stripe_payment_intent_id', 'stripe_charge_id',
                'stripe_customer_id', 'stripe_dashboard_link'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'paid_at', 'updated_at'
            )
        }),
        ('Refunds', {
            'fields': ('refund_history',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'export_payments_csv', 'sync_with_stripe', 'mark_as_completed',
        'generate_payment_report', 'bulk_refund_check'
    ]
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'student', 'teacher', 'gig', 'session_booking'
        ).prefetch_related('refund_requests')
    
    def payment_status_badge(self, obj):
        """Display payment status with enhanced color badge"""
        color_map = {
            'PENDING': '#ff9800',      # Orange
            'PROCESSING': '#2196f3',   # Blue
            'COMPLETED': '#4caf50',    # Green
            'FAILED': '#f44336',       # Red
            'REFUND_REQUESTED': '#9c27b0',  # Purple
            'REFUNDED': '#607d8b',     # Blue Gray
            'CANCELLED': '#424242'     # Dark Gray
        }
        color = color_map.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    payment_status_badge.short_description = 'Status'
    
    def payment_status_badge_display(self, obj):
        """Large status badge for detail view"""
        return self.payment_status_badge(obj)
    payment_status_badge_display.short_description = 'Payment Status'
    
    def student_link(self, obj):
        """Enhanced student link with name"""
        url = reverse('admin:core_user_change', args=[obj.student.id])
        name = obj.student.get_full_name() or obj.student.email
        return format_html('<a href="{}" target="_blank">{}</a>', url, name)
    student_link.short_description = 'Student'
    
    def teacher_link(self, obj):
        """Enhanced teacher link with name"""
        url = reverse('admin:core_user_change', args=[obj.teacher.id])
        name = obj.teacher.get_full_name() or obj.teacher.email
        return format_html('<a href="{}" target="_blank">{}</a>', url, name)
    teacher_link.short_description = 'Teacher'
    
    def booking_link(self, obj):
        """Link to session booking"""
        if obj.session_booking:
            url = reverse('admin:bookings_sessionbooking_change', args=[obj.session_booking.id])
            return format_html('<a href="{}" target="_blank">Booking #{}</a>', url, obj.session_booking.id)
        return '-'
    booking_link.short_description = 'Booking'
    
    def amount_display(self, obj):
        """Display amount as a simple string (no formatting)"""
        return str(obj.amount_dollars)
    amount_display.short_description = 'Amount'
    
    def amount_display_large(self, obj):
        """Large amount display for detail view (no formatting)"""
        return f"{obj.amount_dollars} {obj.currency.upper()}"
    amount_display_large.short_description = 'Payment Amount'
    
    def platform_fee_display(self, obj):
        """Display platform fee as a simple string (no formatting)"""
        return str(Decimal(obj.platform_fee_cents) / 100)
    platform_fee_display.short_description = 'Platform Fee'
    
    def platform_fee_display_large(self, obj):
        """Large platform fee display"""
        fee = Decimal(obj.platform_fee_cents) / 100
        percentage = (fee / obj.amount_dollars) * 100
        return format_html(
            '<div style="font-size: 18px; color: #ff9800;">'
            '${:.2f} ({:.1f}%)</div>',
            fee, percentage
        )
    platform_fee_display_large.short_description = 'Platform Fee'
    
    def calculate_fees(self, obj):
        """Calculate and display all fees breakdown"""
        amount = obj.amount_dollars
        platform_fee = Decimal(obj.platform_fee_cents) / 100
        stripe_fee = amount * Decimal('0.029') + Decimal('0.30')  # Approximate Stripe fee
        net_amount = amount - platform_fee - stripe_fee
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
            '<strong>Fee Breakdown:</strong><br>'
            'Total Amount: <strong>${:.2f}</strong><br>'
            'Platform Fee: <span style="color: #ff9800;">${:.2f}</span><br>'
            'Stripe Fee: <span style="color: #2196f3;">${:.2f}</span><br>'
            'Net to Platform: <span style="color: #4caf50;">${:.2f}</span>'
            '</div>',
            amount, platform_fee, stripe_fee, net_amount
        )
    calculate_fees.short_description = 'Fee Breakdown'
    
    def stripe_link(self, obj):
        """Link to Stripe dashboard"""
        if obj.stripe_payment_intent_id:
            return format_html(
                '<a href="https://dashboard.stripe.com/payments/{}" target="_blank" '
                'style="color: #635bff;">View in Stripe</a>',
                obj.stripe_payment_intent_id
            )
        return '-'
    stripe_link.short_description = 'Stripe'
    
    def stripe_dashboard_link(self, obj):
        """Full Stripe dashboard link for detail view"""
        if obj.stripe_payment_intent_id:
            return format_html(
                '<a href="https://dashboard.stripe.com/payments/{}" target="_blank" '
                'class="button" style="background: #635bff; color: white; padding: 8px 16px; '
                'text-decoration: none; border-radius: 4px;">Open in Stripe Dashboard</a>',
                obj.stripe_payment_intent_id
            )
        return 'No Stripe ID available'
    stripe_dashboard_link.short_description = 'Stripe Dashboard'
    
    def refund_history(self, obj):
        """Display refund history"""
        refunds = obj.refund_requests.all()
        if not refunds:
            return format_html('<em>No refund requests</em>')
        
        html = '<div style="background: #f9f9f9; padding: 10px; border-radius: 4px;">'
        html += '<strong>Refund Requests:</strong><br>'
        
        for refund in refunds:
            status_color = {
                'PENDING': '#ff9800',
                'APPROVED': '#4caf50', 
                'REJECTED': '#f44336',
                'PROCESSED': '#2196f3'
            }.get(refund.status, '#757575')
            
            html += format_html(
                '<div style="margin: 5px 0; padding: 5px; background: white; border-radius: 2px;">'
                '#{}: <span style="color: {}; font-weight: bold;">{}</span> - '
                '${:.2f} - {}</div>',
                refund.id, status_color, refund.status,
                refund.requested_amount_dollars, refund.created_at.strftime('%Y-%m-%d')
            )
        
        html += '</div>'
        return format_html(html)
    refund_history.short_description = 'Refund History'
    
    def session_date(self, obj):
        """Display session date with status"""
        if obj.session_booking and obj.session_booking.scheduled_datetime:
            date_str = obj.session_booking.scheduled_datetime.strftime('%Y-%m-%d %H:%M')
            status = obj.session_booking.status
            status_color = {
                'PENDING': '#ff9800',
                'CONFIRMED': '#2196f3',
                'COMPLETED': '#4caf50',
                'CANCELLED': '#f44336'
            }.get(status, '#757575')
            
            return format_html(
                '{}<br><small style="color: {};">{}</small>',
                date_str, status_color, status
            )
        return '-'
    session_date.short_description = 'Session Date/Status'
    
    # Admin Actions
    def export_payments_csv(self, request, queryset):
        """Export selected payments to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payments_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Student Email', 'Teacher Email', 'Amount', 'Platform Fee',
            'Status', 'Created At', 'Session Date', 'Gig Title', 'Stripe ID'
        ])
        
        for payment in queryset:
            writer.writerow([
                payment.id,
                payment.student.email,
                payment.teacher.email,
                payment.amount_dollars,
                Decimal(payment.platform_fee_cents) / 100,
                payment.status,
                payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                payment.session_booking.scheduled_datetime.strftime('%Y-%m-%d %H:%M:%S') if payment.session_booking and payment.session_booking.scheduled_datetime else '',
                payment.gig.service_title if payment.gig else '',
                payment.stripe_payment_intent_id
            ])
        
        self.message_user(request, f'Exported {queryset.count()} payments to CSV.')
        return response
    export_payments_csv.short_description = "Export selected payments to CSV"
    
    def sync_with_stripe(self, request, queryset):
        """Sync payment status with Stripe"""
        synced_count = 0
        for payment in queryset:
            if payment.stripe_payment_intent_id:
                try:
                    stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                    if stripe_payment.status != payment.status.lower():
                        old_status = payment.status
                        payment.status = stripe_payment.status.upper()
                        payment.save()
                        synced_count += 1
                        self.message_user(
                            request, 
                            f'Payment #{payment.id}: {old_status} → {payment.status}',
                            level=messages.INFO
                        )
                except Exception as e:
                    self.message_user(
                        request, 
                        f'Error syncing payment #{payment.id}: {str(e)}',
                        level=messages.ERROR
                    )
        
        self.message_user(request, f'Synced {synced_count} payments with Stripe.')
    sync_with_stripe.short_description = "Sync selected payments with Stripe"
    
    def mark_as_completed(self, request, queryset):
        """Mark payments as completed"""
        updated = queryset.filter(status='PENDING').update(
            status='COMPLETED',
            paid_at=timezone.now()
        )
        self.message_user(request, f'Marked {updated} payments as completed.')
    mark_as_completed.short_description = "Mark as completed"
    
    def generate_payment_report(self, request, queryset):
        """Generate detailed payment report"""
        total_amount = queryset.aggregate(total=Sum('amount_cents'))['total'] or 0
        total_fees = queryset.aggregate(total=Sum('platform_fee_cents'))['total'] or 0
        
        report = {
            'total_payments': queryset.count(),
            'total_amount': Decimal(total_amount) / 100,
            'total_fees': Decimal(total_fees) / 100,
            'status_breakdown': {},
            'top_teachers': [],
            'recent_payments': []
        }
        
        # Status breakdown
        for status in ['COMPLETED', 'PENDING', 'FAILED', 'REFUNDED']:
            count = queryset.filter(status=status).count()
            if count > 0:
                report['status_breakdown'][status] = count
        
        response = JsonResponse(report, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = 'attachment; filename="payment_report.json"'
        return response
    generate_payment_report.short_description = "Generate payment report (JSON)"
    
    def bulk_refund_check(self, request, queryset):
        """Check refund eligibility for selected payments"""
        eligible_count = 0
        for payment in queryset:
            if payment.status == 'COMPLETED' and not payment.refund_requests.filter(
                status__in=['PENDING', 'APPROVED', 'PROCESSED']
            ).exists():
                eligible_count += 1
        
        self.message_user(
            request, 
            f'{eligible_count} out of {queryset.count()} payments are eligible for refund.'
        )
    bulk_refund_check.short_description = "Check refund eligibility"


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for refund requests with processing capabilities
    """
    list_display = [
        'id', 'status_badge', 'student_link', 'requested_amount_display',
        'payment_link', 'session_info', 'created_at', 'reviewed_at', 'urgency_indicator'
    ]
    list_filter = [
        'status', 'created_at', 'reviewed_at', 'payment__session_booking__status'
    ]
    search_fields = [
        'student__email', 'payment__stripe_payment_intent_id', 'reason',
        'payment__teacher__email'
    ]
    readonly_fields = [
        'payment', 'student', 'requested_amount_cents',
        'stripe_refund_id', 'refunded_amount_cents',
        'created_at', 'refunded_at', 'updated_at', 'payment_details_display',
        'refund_calculation', 'stripe_refund_link',
        'urgency_badge_display', 'status_badge_display', 'requested_amount_display_large'
    ]
    
    fieldsets = (
        ('Refund Overview', {
            'fields': (
                'status_badge_display', 'urgency_badge_display',
                'requested_amount_display_large', 'refund_calculation'
            )
        }),
        ('Request Details', {
            'fields': (
                'payment', 'student', 'reason',
                'requested_amount_cents', 'status', 'payment_details_display'
            )
        }),
        ('Admin Review', {
            'fields': (
                'admin_notes', 'reviewed_by', 'reviewed_at'
            )
        }),
        ('Refund Processing', {
            'fields': (
                'stripe_refund_id', 'refunded_amount_cents', 'refunded_at',
                'stripe_refund_link'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at'
            )
        })
    )
    
    actions = [
        'bulk_approve_refunds', 'bulk_reject_refunds', 'export_refunds_csv',
        'process_approved_refunds', 'send_refund_notifications'
    ]
    
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'payment', 'student', 'payment__teacher', 'payment__session_booking',
            'reviewed_by'
        )
    
    def status_badge(self, obj):
        """Enhanced status badge with icons"""
        status_config = {
            'PENDING': {'color': '#ff9800', 'icon': '⏳'},
            'APPROVED': {'color': '#4caf50', 'icon': '✅'},
            'REJECTED': {'color': '#f44336', 'icon': '❌'},
            'PROCESSED': {'color': '#2196f3', 'icon': '💰'}
        }
        config = status_config.get(obj.status, {'color': '#757575', 'icon': '❓'})
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 12px; font-weight: bold;">'
            '{} {}</span>',
            config['color'], config['icon'], obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def status_badge_display(self, obj):
        """Large status badge for detail view"""
        return format_html(
            '<div style="font-size: 18px;">{}</div>',
            self.status_badge(obj)
        )
    status_badge_display.short_description = 'Refund Status'
    
    def urgency_indicator(self, obj):
        """Show urgency based on request age and amount"""
        days_old = (timezone.now() - obj.created_at).days
        is_large_amount = obj.requested_amount_dollars > 50
        
        if obj.status == 'PENDING':
            if days_old >= 3:
                return format_html('<span style="color: red; font-weight: bold;">🔥 URGENT</span>')
            elif days_old >= 1:
                return format_html('<span style="color: orange;">⚠️ HIGH</span>')
            elif is_large_amount:
                return format_html('<span style="color: blue;">💰 LARGE</span>')
        
        return '-'
    urgency_indicator.short_description = 'Urgency'
    
    def urgency_badge_display(self, obj):
        """Large urgency display for detail view"""
        urgency = self.urgency_indicator(obj)
        if urgency != '-':
            return format_html('<div style="font-size: 16px;">{}</div>', urgency)
        return 'Normal Priority'
    urgency_badge_display.short_description = 'Priority Level'
    
    def student_link(self, obj):
        """Enhanced student link"""
        url = reverse('admin:core_user_change', args=[obj.student.id])
        name = obj.student.get_full_name() or obj.student.email
        return format_html('<a href="{}" target="_blank">{}</a>', url, name)
    student_link.short_description = 'Student'
    
    def payment_link(self, obj):
        """Enhanced payment link with amount (no formatting)"""
        url = reverse('admin:stripe_payments_payment_change', args=[obj.payment.id])
        return format_html(
            '<a href="{}" target="_blank">Payment #{}<br><small>{}</small></a>',
            url, obj.payment.id, obj.payment.amount_dollars
        )
    payment_link.short_description = 'Payment'
    
    def session_info(self, obj):
        """Display session information"""
        booking = obj.payment.session_booking
        if booking:
            status_color = {
                'PENDING': '#ff9800',
                'CONFIRMED': '#2196f3',
                'COMPLETED': '#4caf50',
                'CANCELLED': '#f44336'
            }.get(booking.status, '#757575')
            
            return format_html(
                '<div><strong>{}</strong><br>'
                '<small style="color: {};">{}</small></div>',
                booking.scheduled_datetime.strftime('%Y-%m-%d %H:%M') if booking.scheduled_datetime else 'No date',
                status_color, booking.status
            )
        return '-'
    session_info.short_description = 'Session Info'
    
    def requested_amount_display(self, obj):
        """Display requested amount as a simple string (no formatting)"""
        try:
            percentage = (float(obj.requested_amount_dollars) / float(obj.payment.amount_dollars)) * 100
            percentage_str = f"{percentage:.0f}"
        except Exception:
            percentage_str = "-"
        return f"{obj.requested_amount_dollars} ({percentage_str}% of payment)"
    requested_amount_display.short_description = 'Requested Amount'
    
    def requested_amount_display_large(self, obj):
        """Large amount display for detail view (no formatting)"""
        try:
            percentage = (float(obj.requested_amount_dollars) / float(obj.payment.amount_dollars)) * 100
            percentage_str = f"{percentage:.0f}"
        except Exception:
            percentage_str = "-"
        return f"{obj.requested_amount_dollars} ({percentage_str}% of {obj.payment.amount_dollars} payment)"
    requested_amount_display_large.short_description = 'Refund Amount'
    
    def payment_details_display(self, obj):
        """Comprehensive payment details"""
        payment = obj.payment
        booking = payment.session_booking
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
            '<strong>Payment Details:</strong><br>'
            'Payment ID: #{}<br>'
            'Original Amount: <strong>${:.2f}</strong><br>'
            'Platform Fee: ${:.2f}<br>'
            'Teacher: {}<br>'
            'Session Date: {}<br>'
            'Session Status: <span style="font-weight: bold;">{}</span><br>'
            'Payment Status: <span style="font-weight: bold;">{}</span>'
            '</div>',
            payment.id, payment.amount_dollars,
            Decimal(payment.platform_fee_cents) / 100,
            payment.teacher.get_full_name() or payment.teacher.email,
            booking.scheduled_datetime.strftime('%Y-%m-%d %H:%M') if booking and booking.scheduled_datetime else 'N/A',
            booking.status if booking else 'N/A',
            payment.status
        )
    payment_details_display.short_description = 'Payment Information'
    
    def refund_calculation(self, obj):
        """Show refund calculation breakdown"""
        original = obj.payment.amount_dollars
        requested = obj.requested_amount_dollars
        platform_fee_portion = (Decimal(obj.payment.platform_fee_cents) / 100) * (requested / original)
        
        return format_html(
            '<div style="background: #e3f2fd; padding: 10px; border-radius: 4px;">'
            '<strong>Refund Breakdown:</strong><br>'
            'Requested: <strong>${:.2f}</strong><br>'
            'Platform Fee Portion: ${:.2f}<br>'
            'Net Refund to Student: <strong>${:.2f}</strong><br>'
            'Stripe Fee: ~${:.2f} (non-refundable)'
            '</div>',
            requested, platform_fee_portion, requested,
            requested * Decimal('0.029') + Decimal('0.30')
        )
    refund_calculation.short_description = 'Refund Calculation'
    
    def stripe_refund_link(self, obj):
        """Link to Stripe refund"""
        if obj.stripe_refund_id:
            return format_html(
                '<a href="https://dashboard.stripe.com/refunds/{}" target="_blank" '
                'class="button" style="background: #635bff; color: white; padding: 8px 16px; '
                'text-decoration: none; border-radius: 4px;">View in Stripe</a>',
                obj.stripe_refund_id
            )
        return 'Not processed yet'
    stripe_refund_link.short_description = 'Stripe Refund'
    
    # Admin Actions
    def bulk_approve_refunds(self, request, queryset):
        """Bulk approve refund requests"""
        pending_refunds = queryset.filter(status='PENDING')
        updated = pending_refunds.update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_notes='Bulk approved by admin'
        )
        self.message_user(request, f'Approved {updated} refund requests.')
    bulk_approve_refunds.short_description = "Approve selected refund requests"
    
    def bulk_reject_refunds(self, request, queryset):
        """Bulk reject refund requests"""
        pending_refunds = queryset.filter(status='PENDING')
        updated = pending_refunds.update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            admin_notes='Bulk rejected by admin'
        )
        self.message_user(request, f'Rejected {updated} refund requests.')
    bulk_reject_refunds.short_description = "Reject selected refund requests"
    
    def process_approved_refunds(self, request, queryset):
        """Process approved refunds through Stripe"""
        approved_refunds = queryset.filter(status='APPROVED')
        processed_count = 0
        
        for refund in approved_refunds:
            try:
                StripePaymentService.create_refund(refund)
                processed_count += 1
                self.message_user(
                    request,
                    f'Processed refund #{refund.id} - ${refund.requested_amount_dollars}',
                    level=messages.SUCCESS
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Failed to process refund #{refund.id}: {str(e)}',
                    level=messages.ERROR
                )
        
        self.message_user(request, f'Successfully processed {processed_count} refunds.')
    process_approved_refunds.short_description = "Process approved refunds via Stripe"
    
    def export_refunds_csv(self, request, queryset):
        """Export refund requests to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="refund_requests.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Status', 'Student Email', 'Requested Amount', 'Original Payment',
            'Reason', 'Created At', 'Reviewed By', 'Reviewed At', 'Refunded At'
        ])
        
        for refund in queryset:
            writer.writerow([
                refund.id,
                refund.status,
                refund.student.email,
                refund.requested_amount_dollars,
                refund.payment.amount_dollars,
                refund.reason[:100] + '...' if len(refund.reason) > 100 else refund.reason,
                refund.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                refund.reviewed_by.email if refund.reviewed_by else '',
                refund.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if refund.reviewed_at else '',
                refund.refunded_at.strftime('%Y-%m-%d %H:%M:%S') if refund.refunded_at else ''
            ])
        
        self.message_user(request, f'Exported {queryset.count()} refund requests to CSV.')
        return response
    export_refunds_csv.short_description = "Export selected refunds to CSV"


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
