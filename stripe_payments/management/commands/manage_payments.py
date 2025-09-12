"""
Django management command for comprehensive payment management
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import datetime, timedelta
import stripe
from django.conf import settings

from stripe_payments.models import Payment, RefundRequest, PaymentAnalytics, StripeCustomer
from stripe_payments.services import StripePaymentService


class Command(BaseCommand):
    help = 'Comprehensive payment management and sync operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-stripe',
            action='store_true',
            help='Sync all payments with Stripe API'
        )
        parser.add_argument(
            '--generate-analytics',
            action='store_true',
            help='Generate daily payment analytics'
        )
        parser.add_argument(
            '--process-pending-refunds',
            action='store_true',
            help='Process all approved refund requests'
        )
        parser.add_argument(
            '--cleanup-old-data',
            action='store_true',
            help='Clean up old payment data (older than 1 year)'
        )
        parser.add_argument(
            '--payment-report',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            help='Generate payment report for specified period'
        )
        parser.add_argument(
            '--fix-inconsistencies',
            action='store_true',
            help='Fix data inconsistencies between local and Stripe data'
        )
        
    def handle(self, *args, **options):
        """Handle the management command"""
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        if options['sync_stripe']:
            self.sync_with_stripe()
            
        if options['generate_analytics']:
            self.generate_analytics()
            
        if options['process_pending_refunds']:
            self.process_pending_refunds()
            
        if options['cleanup_old_data']:
            self.cleanup_old_data()
            
        if options['payment_report']:
            self.generate_payment_report(options['payment_report'])
            
        if options['fix_inconsistencies']:
            self.fix_inconsistencies()
            
        if not any(options.values()):
            self.print_payment_overview()
    
    def sync_with_stripe(self):
        """Sync all payments with Stripe API"""
        self.stdout.write('🔄 Syncing payments with Stripe...')
        
        payments = Payment.objects.filter(stripe_payment_intent_id__isnull=False)
        synced_count = 0
        error_count = 0
        
        for payment in payments:
            try:
                stripe_payment = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
                
                # Update status if different
                stripe_status = stripe_payment.status.upper()
                if payment.status != stripe_status:
                    self.stdout.write(
                        f'  📝 Payment #{payment.id}: {payment.status} → {stripe_status}'
                    )
                    payment.status = stripe_status
                    payment.save()
                    synced_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error syncing payment #{payment.id}: {str(e)}')
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Synced {synced_count} payments. {error_count} errors.')
        )
    
    def generate_analytics(self):
        """Generate daily payment analytics"""
        self.stdout.write('📊 Generating payment analytics...')
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get yesterday's payments
        payments = Payment.objects.filter(created_at__date=yesterday)
        
        if not payments.exists():
            self.stdout.write('  ℹ️  No payments found for yesterday')
            return
        
        # Calculate metrics
        total_payments = payments.count()
        successful_payments = payments.filter(status='COMPLETED').count()
        failed_payments = payments.filter(status='FAILED').count()
        total_amount = payments.aggregate(Sum('amount_cents'))['amount_cents__sum'] or 0
        refund_requests = RefundRequest.objects.filter(created_at__date=yesterday).count()
        
        # Create or update analytics record
        analytics, created = PaymentAnalytics.objects.get_or_create(
            date=yesterday,
            defaults={
                'total_payments_count': total_payments,
                'successful_payments_count': successful_payments,
                'failed_payments_count': failed_payments,
                'total_amount_cents': total_amount,
                'refund_requests_count': refund_requests,
            }
        )
        
        if not created:
            analytics.total_payments_count = total_payments
            analytics.successful_payments_count = successful_payments
            analytics.failed_payments_count = failed_payments
            analytics.total_amount_cents = total_amount
            analytics.refund_requests_count = refund_requests
            analytics.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Generated analytics for {yesterday}: '
                f'{total_payments} payments, ${Decimal(total_amount)/100:.2f} total'
            )
        )
    
    def process_pending_refunds(self):
        """Process all approved refund requests"""
        self.stdout.write('💰 Processing approved refunds...')
        
        approved_refunds = RefundRequest.objects.filter(status='APPROVED')
        
        if not approved_refunds.exists():
            self.stdout.write('  ℹ️  No approved refunds to process')
            return
        
        processed_count = 0
        error_count = 0
        
        for refund in approved_refunds:
            try:
                result = StripePaymentService.create_refund(refund)
                self.stdout.write(
                    f'  ✅ Processed refund #{refund.id}: ${refund.requested_amount_dollars}'
                )
                processed_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error processing refund #{refund.id}: {str(e)}')
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Processed {processed_count} refunds. {error_count} errors.')
        )
    
    def cleanup_old_data(self):
        """Clean up old payment data"""
        self.stdout.write('🧹 Cleaning up old payment data...')
        
        cutoff_date = timezone.now() - timedelta(days=365)  # 1 year ago
        
        # Count old records
        old_payments = Payment.objects.filter(created_at__lt=cutoff_date)
        old_refunds = RefundRequest.objects.filter(created_at__lt=cutoff_date)
        old_analytics = PaymentAnalytics.objects.filter(date__lt=cutoff_date.date())
        
        payment_count = old_payments.count()
        refund_count = old_refunds.count()
        analytics_count = old_analytics.count()
        
        if payment_count == 0 and refund_count == 0 and analytics_count == 0:
            self.stdout.write('  ℹ️  No old data to clean up')
            return
        
        # Ask for confirmation
        confirm = input(f'Delete {payment_count} payments, {refund_count} refunds, '
                       f'and {analytics_count} analytics records? (y/N): ')
        
        if confirm.lower() == 'y':
            # Delete old records
            old_analytics.delete()
            old_refunds.delete() 
            old_payments.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Cleaned up old data: {payment_count} payments, '
                                 f'{refund_count} refunds, {analytics_count} analytics')
            )
        else:
            self.stdout.write('  ℹ️  Cleanup cancelled')
    
    def generate_payment_report(self, period):
        """Generate payment report for specified period"""
        self.stdout.write(f'📈 Generating {period} payment report...')
        
        today = timezone.now().date()
        
        if period == 'daily':
            start_date = today
            end_date = today
        elif period == 'weekly':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == 'monthly':
            start_date = today - timedelta(days=30)
            end_date = today
        
        payments = Payment.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Calculate metrics
        total_count = payments.count()
        successful_count = payments.filter(status='COMPLETED').count()
        failed_count = payments.filter(status='FAILED').count()
        total_amount = payments.aggregate(Sum('amount_cents'))['amount_cents__sum'] or 0
        platform_fees = payments.aggregate(Sum('platform_fee_cents'))['platform_fee_cents__sum'] or 0
        
        success_rate = (successful_count / total_count * 100) if total_count > 0 else 0
        avg_amount = (Decimal(total_amount) / 100 / total_count) if total_count > 0 else 0
        
        # Print report
        self.stdout.write(f'\n📊 {period.upper()} PAYMENT REPORT')
        self.stdout.write(f'Period: {start_date} to {end_date}')
        self.stdout.write('=' * 50)
        self.stdout.write(f'Total Payments: {total_count}')
        self.stdout.write(f'Successful: {successful_count} ({success_rate:.1f}%)')
        self.stdout.write(f'Failed: {failed_count}')
        self.stdout.write(f'Total Revenue: ${Decimal(total_amount)/100:.2f}')
        self.stdout.write(f'Platform Fees: ${Decimal(platform_fees)/100:.2f}')
        self.stdout.write(f'Average Payment: ${avg_amount:.2f}')
        
        # Top teachers by revenue
        top_teachers = payments.filter(status='COMPLETED').values(
            'teacher__email'
        ).annotate(
            revenue=Sum('amount_cents'),
            payment_count=Count('id')
        ).order_by('-revenue')[:5]
        
        if top_teachers:
            self.stdout.write(f'\n🏆 TOP TEACHERS BY REVENUE:')
            for i, teacher in enumerate(top_teachers, 1):
                revenue = Decimal(teacher['revenue']) / 100
                self.stdout.write(f'{i}. {teacher["teacher__email"]}: ${revenue:.2f} ({teacher["payment_count"]} payments)')
        
        self.stdout.write('=' * 50)
    
    def fix_inconsistencies(self):
        """Fix data inconsistencies"""
        self.stdout.write('🔧 Fixing data inconsistencies...')
        
        fixed_count = 0
        
        # Fix payments without proper amounts
        payments_without_amount = Payment.objects.filter(amount_cents=0)
        for payment in payments_without_amount:
            if payment.hourly_rate_cents and payment.session_duration_hours:
                calculated_amount = int(payment.hourly_rate_cents * payment.session_duration_hours)
                payment.amount_cents = calculated_amount
                payment.save()
                fixed_count += 1
                self.stdout.write(f'  ✅ Fixed amount for payment #{payment.id}')
        
        # Fix missing platform fees
        payments_without_fees = Payment.objects.filter(platform_fee_cents=0, amount_cents__gt=0)
        for payment in payments_without_fees:
            session_cost = Decimal(payment.amount_cents) / 100 / 1.05  # Reverse calculate
            platform_fee = session_cost * Decimal('0.05')
            payment.platform_fee_cents = int(platform_fee * 100)
            payment.save()
            fixed_count += 1
            self.stdout.write(f'  ✅ Fixed platform fee for payment #{payment.id}')
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Fixed {fixed_count} data inconsistencies')
        )
    
    def print_payment_overview(self):
        """Print overall payment system overview"""
        self.stdout.write('💳 PAYMENT SYSTEM OVERVIEW')
        self.stdout.write('=' * 50)
        
        # Overall stats
        total_payments = Payment.objects.count()
        completed_payments = Payment.objects.filter(status='COMPLETED').count()
        total_revenue = Payment.objects.filter(status='COMPLETED').aggregate(
            Sum('amount_cents')
        )['amount_cents__sum'] or 0
        
        pending_refunds = RefundRequest.objects.filter(status='PENDING').count()
        total_customers = StripeCustomer.objects.count()
        
        self.stdout.write(f'Total Payments: {total_payments}')
        self.stdout.write(f'Completed Payments: {completed_payments}')
        self.stdout.write(f'Total Revenue: ${Decimal(total_revenue)/100:.2f}')
        self.stdout.write(f'Pending Refunds: {pending_refunds}')
        self.stdout.write(f'Total Customers: {total_customers}')
        
        # Recent activity
        recent_payments = Payment.objects.order_by('-created_at')[:5]
        if recent_payments:
            self.stdout.write(f'\n📈 RECENT PAYMENTS:')
            for payment in recent_payments:
                self.stdout.write(
                    f'  #{payment.id}: ${payment.amount_dollars:.2f} - {payment.status} - {payment.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
        
        self.stdout.write('=' * 50)
        self.stdout.write('Use --help to see available management options')
