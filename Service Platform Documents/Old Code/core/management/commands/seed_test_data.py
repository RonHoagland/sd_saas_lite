import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from audit.models import Session, UserTransaction
from backup.models import Backup, BackupSettings
from core.models import Preference, ValueList, ValueListItem

class Command(BaseCommand):
    help = 'Seeds the database with test data for Functional and Performance testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding test data...')

        # 1. Users
        self.stdout.write('Creating users...')
        # Superuser
        admin, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@brixa.com', 'is_staff': True, 'is_superuser': True})
        if _: admin.set_password('admin123'); admin.save()
        
        # Staff
        staff, _ = User.objects.get_or_create(username='manager', defaults={'email': 'manager@brixa.com', 'is_staff': True})
        if _: staff.set_password('staff123'); staff.save()

        # Regular Users
        created_count = 0
        for i in range(1, 51):
            u, created = User.objects.get_or_create(username=f'user{i}', defaults={'email': f'user{i}@example.com'})
            if created:
                u.set_password('user123')
                u.save()
                created_count += 1
        self.stdout.write(f'- Created {created_count} regular users')

        # 2. Preferences
        self.stdout.write('Creating preferences...')
        defaults = [
            ('general_site_name', 'BrixaWares Platform', 'String', 'Site Title'),
            ('security_session_timeout', '30', 'Integer', 'Session Timeout (minutes)'),
            ('ui_theme_color', '#2563eb', 'String', 'Primary Theme Color'),
        ]
        system_user = User.objects.get(username='admin')
        for key, val, dtype, name in defaults:
            Preference.objects.get_or_create(
                key=key,
                defaults={
                    'value': val,
                    'default_value': val,
                    'data_type': dtype.lower(),
                    'name': name,
                    'description': f'Test preference for {name}',
                    'created_by': system_user,
                    'updated_by': system_user
                }
            )

        # 3. Backups
        self.stdout.write('Creating mock backups...')
        BackupSettings.get_settings() # Ensure settings exist
        for i in range(5):
            ts = timezone.now() - timedelta(days=i)
            status = 'success' if i > 0 else 'failed'
            Backup.objects.get_or_create(
                backup_id=f'backup_{ts.strftime("%Y%m%d_%H%M%S")}',
                defaults={
                    'backup_path': f'/tmp/backups/backup_{i}',
                    'status': status,
                    'backup_timestamp': ts,
                    'start_time': ts,
                    'end_time': ts + timedelta(seconds=120),
                    'database_size_bytes': 1024 * 1024 * (50 + i),
                    'files_size_bytes': 1024 * 1024 * (200 + i * 10),
                    'created_by': system_user,
                    'updated_by': system_user
                }
            )

        # 4. Audit Logs
        self.stdout.write('Creating audit logs...')
        users = list(User.objects.all())
        session_count = 0
        trans_count = 0
        for i in range(100):
            u = random.choice(users)
            ts = timezone.now() - timedelta(hours=random.randint(1, 100))
            
            # Create Session
            s = Session.objects.create(
                user=u,
                auth_result='success',
                started_at=ts,
                ended_at=ts + timedelta(minutes=random.randint(5, 60)),
                end_reason='logout',
                ip_address=f'192.168.1.{random.randint(1, 255)}'
            )
            session_count += 1

            # Create Transaction
            if random.random() > 0.5:
                UserTransaction.objects.create(
                    session=s,
                    user=u,
                    event_ts=ts + timedelta(minutes=random.randint(1, 5)),
                    event_type=random.choice(['create', 'delete']),
                    entity_type=random.choice(['Client', 'Invoice', 'Project']),
                    entity_id=system_user.id, # Just a valid UUID
                    summary=f'Test transaction {i}',
                    reason_text='Automated test'
                )
                trans_count += 1
        
        self.stdout.write(f'- Created {session_count} sessions and {trans_count} transactions')
        self.stdout.write(self.style.SUCCESS('Test data seeded successfully.'))
