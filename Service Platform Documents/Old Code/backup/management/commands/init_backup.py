"""
Initialize backup settings.

Creates default backup settings and configuration if not already present.
"""

from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from backup.models import BackupSettings


class Command(BaseCommand):
    help = 'Initialize backup settings with defaults'
    
    def handle(self, *args, **options):
        # Check if settings already exist
        existing = BackupSettings.objects.first()
        if existing:
            self.stdout.write(
                self.style.WARNING('Backup settings already initialized')
            )
            return
        
        # Get or create a system user for audit
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={'email': 'system@brixacore.local'}
        )
        
        # Create default settings
        default_backup_path = str(Path.home() / 'BrixaWares_Backups')
        
        settings = BackupSettings(
            backup_path=default_backup_path,
            schedule_time='02:00',
            retention_count=10,
            is_enabled=True,
            created_by=system_user,
            updated_by=system_user,
        )
        
        try:
            settings.full_clean()
            settings.save()
            
            self.stdout.write(
                self.style.SUCCESS('✓ Backup settings initialized')
            )
            self.stdout.write(f'  Path: {settings.backup_path}')
            self.stdout.write(f'  Schedule: {settings.schedule_time} daily')
            self.stdout.write(f'  Retention: {settings.retention_count} backups')
            
        except Exception as e:
            raise CommandError(f'Failed to initialize backup settings: {str(e)}')
