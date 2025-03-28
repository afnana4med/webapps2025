from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.management import call_command
from payapp.models import Account
from django.db.utils import OperationalError, ProgrammingError

class Command(BaseCommand):
    help = 'Initialize database with required initial data'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database with initial data...')
        
        # First, apply migrations to ensure all tables exist
        # Apply migrations explicitly for all apps
        self.stdout.write('Applying migrations...')
        call_command('migrate', 'admin', interactive=False)
        call_command('migrate', 'auth', interactive=False)
        call_command('migrate', 'contenttypes', interactive=False)
        call_command('migrate', 'sessions', interactive=False)
        call_command('migrate', 'payapp', interactive=False)
        self.stdout.write(self.style.SUCCESS('Migrations applied'))
        
        # Create admin user if it doesn't exist
        try:
            if not User.objects.filter(username='admin').exists():
                admin = User.objects.create_superuser(
                    username='admin1',
                    email='admin@example.com',
                    password='admin1'
                )
                
                # Create the account with error handling
                try:
                    # Make sure the table exists first
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payapp_account';")
                        if not cursor.fetchone():
                            self.stdout.write(self.style.WARNING('payapp_account table does not exist. Check migrations.'))
                            raise OperationalError("Table payapp_account doesn't exist")
                    
                    Account.objects.create(
                        user=admin,
                        currency='GBP',
                        balance=750.00
                    )
                    self.stdout.write(self.style.SUCCESS('Admin account created with initial balance'))
                except (OperationalError, ProgrammingError) as e:
                    self.stdout.write(self.style.WARNING(f'Could not create Account: {e}'))
                    self.stdout.write(self.style.WARNING('Admin user created without Account'))
                
                self.stdout.write(self.style.SUCCESS('Admin user created'))
            else:
                self.stdout.write('Admin user already exists')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin user: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Database initialized successfully'))