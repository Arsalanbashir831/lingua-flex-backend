from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser for LinguaFlex admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the superuser',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
        )

    def handle(self, *args, **options):
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')
        
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password
            )
            user.first_name = "Admin"
            user.last_name = "User"
            user.role = User.Role.ADMIN
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser with email: {email}'
                )
            )
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(
                    f'User with email {email} already exists'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error creating superuser: {str(e)}'
                )
            )
