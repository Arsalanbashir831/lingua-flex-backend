"""
Django management command to sync user roles from Django to Supabase metadata
Usage: python manage.py sync_roles_to_supabase
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import TeacherProfile
from supabase import create_client
import os
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Sync user roles from Django to Supabase user metadata'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Sync only a specific user by email',
        )

    def handle(self, *args, **options):
        # Initialize Supabase client
        try:
            supabase_url = getattr(settings, 'SUPABASE_URL', os.getenv('SUPABASE_URL'))
            supabase_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
            
            if not supabase_url or not supabase_key:
                self.stdout.write(
                    self.style.ERROR('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set')
                )
                return
            
            supabase = create_client(supabase_url, supabase_key)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to initialize Supabase client: {e}')
            )
            return

        # Get users to sync
        if options['email']:
            users = User.objects.filter(email=options['email'])
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'No user found with email: {options["email"]}')
                )
                return
        else:
            users = User.objects.all()

        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        self.stdout.write(f'Processing {users.count()} users...')
        
        updated_count = 0
        error_count = 0
        
        for user in users:
            try:
                # Determine user role from Django
                has_teacher_profile = TeacherProfile.objects.filter(user=user).exists()
                django_role = 'TEACHER' if has_teacher_profile else 'STUDENT'
                
                # Try to find the user in Supabase by email
                try:
                    # Note: This might need adjustment based on your Supabase setup
                    # You might need to list all users and filter by email
                    supabase_users = supabase.auth.admin.list_users()
                    supabase_user = None
                    
                    for su_user in supabase_users:
                        if su_user.email == user.email:
                            supabase_user = su_user
                            break
                    
                    if not supabase_user:
                        self.stdout.write(
                            self.style.WARNING(f'User not found in Supabase: {user.email}')
                        )
                        continue
                    
                    # Get current metadata
                    current_metadata = supabase_user.user_metadata or {}
                    current_role = current_metadata.get('role')
                    
                    # Check if update is needed
                    if current_role == django_role:
                        self.stdout.write(f'✓ {user.email}: Role already correct ({django_role})')
                        continue
                    
                    # Prepare updated metadata
                    updated_metadata = current_metadata.copy()
                    updated_metadata['role'] = django_role
                    
                    # Add name information if available
                    if hasattr(user, 'first_name') and user.first_name:
                        updated_metadata['first_name'] = user.first_name
                    if hasattr(user, 'last_name') and user.last_name:
                        updated_metadata['last_name'] = user.last_name
                    
                    if dry_run:
                        self.stdout.write(
                            f'Would update {user.email}: {current_role} → {django_role}'
                        )
                    else:
                        # Update user metadata in Supabase
                        supabase.auth.admin.update_user_by_id(
                            supabase_user.id,
                            {"user_metadata": updated_metadata}
                        )
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Updated {user.email}: {current_role} → {django_role}'
                            )
                        )
                        updated_count += 1
                
                except Exception as supabase_error:
                    self.stdout.write(
                        self.style.ERROR(f'Supabase error for {user.email}: {supabase_error}')
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {user.email}: {e}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETED'))
        else:
            self.stdout.write(self.style.SUCCESS(f'SYNC COMPLETED'))
            self.stdout.write(f'Users updated: {updated_count}')
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors encountered: {error_count}'))
        
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Test the chats endpoint to verify role detection')
        self.stdout.write('2. Run the test_improved_role_detection.py script')
        self.stdout.write('3. Consider adding this command to a scheduled task for ongoing sync')
