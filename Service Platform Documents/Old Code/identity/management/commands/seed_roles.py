from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from identity.models import Role

User = get_user_model()

class Command(BaseCommand):
    help = 'Ensures the 3 mandatory system roles exist: Administrator, Worker, Read-Only'

    def handle(self, *args, **options):
        self.stdout.write('Seeding system roles...')
        
        # Get a system user for attribution (usually the first superuser)
        system_user = User.objects.filter(is_superuser=True).first()
        if not system_user:
            self.stdout.write(self.style.WARNING("No superuser found to attribute these roles to. Creating roles with NULL attribution (if allowed) or failing."))
            # In strict mode, we might want to fail, but for seeding we can try to proceed if models allow nullable.
            # However, BaseModel fields created_by/updated_by are usually required.
            # Let's try to get ANY user or fail gracefully.
            system_user = User.objects.first()
            
        if not system_user:
             self.stdout.write(self.style.ERROR("No users found at all. Run 'seed_test_data' or create a superuser first."))
             return

        roles_to_seed = [
            {
                'key': 'administrator',
                'name': 'Administrator',
                'description': 'Full system access. Can manage users, roles, and settings.',
            },
            {
                'key': 'worker',
                'name': 'Worker',
                'description': 'Operational access. Can create/edit/delete business records but cannot access Admin Area.',
            },
            {
                'key': 'read_only',
                'name': 'Read-Only',
                'description': 'View-only access. Cannot create, edit, or delete any records.',
            }
        ]

        with transaction.atomic():
            for role_data in roles_to_seed:
                role, created = Role.objects.get_or_create(
                    key=role_data['key'],
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description'],
                        'is_system': True,
                        'created_by': system_user,
                        'updated_by': system_user
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created role: {role.name}"))
                else:
                    # Update metadata just in case
                    role.name = role_data['name']
                    role.description = role_data['description']
                    role.is_system = True # Enforce system status
                    role.save()
                    self.stdout.write(f"Updated role: {role.name}")
        
        self.stdout.write(self.style.SUCCESS('Role seeding complete.'))
