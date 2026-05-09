
from django.core.management.base import BaseCommand
from identity.models import Role

class Command(BaseCommand):
    help = 'Initializes the standard set of system roles (Lite).'

    def handle(self, *args, **options):
        self.stdout.write('Initializing system roles...')
        
        # Standard Lite Roles
        roles = [
            {
                'key': 'owner',
                'name': 'Owner',
                'description': 'Full access to everything, including billing and destructive actions.',
                'is_system': True
            },
            {
                'key': 'admin',
                'name': 'Administrator',
                'description': 'Administrative access to system configuration and user management.',
                'is_system': True
            },
            {
                'key': 'worker',
                'name': 'Worker',
                'description': 'Standard operational access (Create/Edit/Process).',
                'is_system': True
            },
            {
                'key': 'read_only',
                'name': 'Read Only',
                'description': 'View-only access to data.',
                'is_system': True
            },
        ]

        # Get System User
        from django.contrib.auth import get_user_model
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create one first.'))
            return

        created_count = 0
        updated_count = 0

        for r in roles:
            obj, created = Role.objects.update_or_create(
                key=r['key'],
                defaults={
                    'name': r['name'],
                    'description': r['description'],
                    'is_system': r['is_system'],
                    'created_by': system_user,
                    'updated_by': system_user
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'+ Created role: {r["name"]} ({r["key"]})'))
            else:
                updated_count += 1
                self.stdout.write(f'• Updated role: {r["name"]}')

        self.stdout.write(self.style.SUCCESS(f'Role initialization complete. Created: {created_count}, Updated: {updated_count}'))
