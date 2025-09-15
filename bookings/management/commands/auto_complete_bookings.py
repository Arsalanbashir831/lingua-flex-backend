from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from bookings.models import SessionBooking
from stripe_payments.models import Payment
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Automatically mark bookings as completed when session ends, payment is made, and status is confirmed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        
        now = timezone.now()
        
        # Find bookings eligible for auto-completion
        eligible_bookings = SessionBooking.objects.filter(
            status='CONFIRMED',  # Only confirmed bookings
            end_time__lte=now,   # Session has ended
            payment__status='COMPLETED',  # Payment is complete
            payment__paid_at__isnull=False  # Payment timestamp exists
        ).select_related('payment', 'student', 'teacher', 'gig')
        
        if verbose or dry_run:
            self.stdout.write(
                f"Found {eligible_bookings.count()} bookings eligible for auto-completion"
            )
        
        completed_count = 0
        
        for booking in eligible_bookings:
            try:
                with transaction.atomic():
                    if dry_run:
                        self.stdout.write(
                            f"[DRY RUN] Would complete booking {booking.id}: "
                            f"{booking.student.email} -> {booking.teacher.email} "
                            f"(ended at {booking.end_time})"
                        )
                    else:
                        # Mark booking as completed
                        booking.status = 'COMPLETED'
                        booking.save(update_fields=['status', 'updated_at'])
                        
                        # Also update payment status to ensure consistency
                        if booking.payment and booking.payment.status != 'COMPLETED':
                            booking.payment.status = 'COMPLETED'
                            booking.payment.save(update_fields=['status', 'updated_at'])
                        
                        completed_count += 1
                        
                        if verbose:
                            self.stdout.write(
                                f"Completed booking {booking.id}: "
                                f"{booking.student.email} -> {booking.teacher.email} "
                                f"(${booking.payment.amount_dollars})"
                            )
                        
                        logger.info(f"Auto-completed booking {booking.id}")
                        
            except Exception as e:
                error_msg = f"Error processing booking {booking.id}: {str(e)}"
                self.stderr.write(error_msg)
                logger.error(error_msg)
                continue
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[DRY RUN] Would have completed {eligible_bookings.count()} bookings"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully completed {completed_count} bookings"
                )
            )
        
        # Log summary
        logger.info(f"Auto-completion run: {completed_count} bookings completed")