from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from identity.models import Role

class Command(BaseCommand):
    help = 'Restores missing system roles (Administrator, Worker, Read-Only)'

    def handle(self, *args, **options):
        User = get_user_model()
        # Ensure we have a system user for 'created_by' audit
        system_user, _ = User.objects.get_or_create(username='system')
        
        roles_to_create = [
            {
                'key': 'administrator',
                'name': 'Administrator',
                'description': 'Full system access and configuration privileges.',
                'is_system': True
            },
            {
                'key': 'worker',
                'name': 'Worker',
                'description': 'Standard access to day-to-day operations.',
                'is_system': True
            },
            {
                'key': 'read_only',
                'name': 'Read Only',
                'description': 'View-only access to system data.',
                'is_system': True
            }
        ]
        
        created_count = 0
        for r_data in roles_to_create:
            role, created = Role.objects.get_or_create(
                key=r_data['key'],
                defaults={
                    'name': r_data['name'],
                    'description': r_data['description'],
                    'is_system': r_data['is_system'],
                    'created_by': system_user,
                    'updated_by': system_user
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.name} ({role.key})"))
                created_count += 1
            else:
                self.stdout.write(f"Role already exists: {role.name} ({role.key})")
                
        self.stdout.write(self.style.SUCCESS(f"Role restoration complete. Created {created_count} new roles."))
