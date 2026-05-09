# staff/management/commands/create_system_user.py
# Creates a ServizDesk system user (StaffUser) with full admin access.
#
# System users are SD employees that can cross tenant boundaries and have
# full access to the Django /admin/ interface. They authenticate with their
# email address (not username) at /admin/login/.
#
# Usage:
#   python manage.py create_system_user --email admin@servizdesk.com --name "Your Name"
#   python manage.py create_system_user --email admin@servizdesk.com --name "Your Name" --password secret

import getpass

from django.core.management.base import BaseCommand, CommandError

from staff.models import StaffUser


class Command(BaseCommand):
    help = 'Create a ServizDesk system user (cross-tenant admin account).'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email address.')
        parser.add_argument('--name', required=True, help='Display name.')
        parser.add_argument('--username', help='Optional short login handle (no "@"). Used in addition to email at login.')
        parser.add_argument('--password', help='Password (prompted securely if omitted).')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        name = options['name'].strip()
        username = options.get('username')
        if username:
            username = username.strip().lower()
            if '@' in username:
                raise CommandError('--username must not contain "@". Use --email for that.')
        password = options.get('password')

        if StaffUser.objects.filter(email=email).exists():
            raise CommandError(f'A system user with email "{email}" already exists.')
        if username and StaffUser.objects.filter(username=username).exists():
            raise CommandError(f'A system user with username "{username}" already exists.')

        if not password:
            password = getpass.getpass('Password: ')
            confirm = getpass.getpass('Password (again): ')
            if password != confirm:
                raise CommandError('Passwords do not match.')

        if len(password) < 8:
            raise CommandError('Password must be at least 8 characters.')

        user = StaffUser.objects.create_user(
            email=email, name=name, password=password, username=username,
        )
        # is_superuser and is_staff default to True on StaffUser — no explicit set needed.

        login_label = f'`{user.username}` or `{user.email}`' if user.username else f'`{user.email}`'
        self.stdout.write(
            self.style.SUCCESS(
                f'System user created: {user.name} <{user.email}>\n'
                f'Log in at /admin/ or at the tenant workspace login using {login_label}.'
            )
        )
