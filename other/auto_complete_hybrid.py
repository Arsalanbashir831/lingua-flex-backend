# Modified Django Management Command (calls Supabase function)

from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Calls Supabase database function to auto-complete bookings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        try:
            # Call the Supabase database function directly
            with connection.cursor() as cursor:
                cursor.execute("SELECT auto_complete_expired_bookings()")
                
            if verbose:
                self.stdout.write("Database function executed successfully")
                
            self.stdout.write(
                self.style.SUCCESS("Auto-completion completed via database function")
            )
            
            logger.info("Auto-completion via database function completed")
            
        except Exception as e:
            error_msg = f"Error calling database function: {str(e)}"
            self.stderr.write(error_msg)
            logger.error(error_msg)