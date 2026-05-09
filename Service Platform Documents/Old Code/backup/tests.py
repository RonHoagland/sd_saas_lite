from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.core.exceptions import ValidationError
from unittest.mock import patch, MagicMock
from datetime import datetime, time, timedelta, timezone as dt_timezone
from pathlib import Path
import shutil
import tempfile
from django.contrib.auth.models import User

from backup.models import BackupSettings, Backup, BackupLog

from core.models import Preference
import zoneinfo

class BackupSystemTests(TestCase):
    def setUp(self):
        # Create a temp directory for backups
        self.temp_dir = tempfile.mkdtemp()
        
        # Create system user
        self.user = User.objects.create_user('system', 'system@test.com', 'password')
        
        self.settings = BackupSettings.get_settings()
        self.settings.backup_path = self.temp_dir
        self.settings.schedule_time = time(2, 0)  # 02:00 AM
        self.settings.is_enabled = True
        self.settings.save()
        
        # Default Preference (UTC)
        Preference.objects.create(
            key='loc_timezone', 
            name='Timezone', 
            data_type='string', 
            value='UTC',
            default_value='UTC'
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_settings_validation(self):
        """Test that settings enforce rules."""
        self.settings.retention_count = 1
        with self.assertRaises(ValidationError):
            self.settings.full_clean()
        
        self.settings.retention_count = 10
        self.settings.full_clean()  # Should be fine

    @patch('backup.management.commands.backup.Command._backup_database')
    @patch('backup.management.commands.backup.Command._backup_files')
    def test_manual_backup(self, mock_files, mock_db):
        """Test the manual backup command."""
        # Setup mocks to return dummy values
        mock_db.return_value = (Path('db.gz'), 1024)
        mock_files.return_value = (Path('files.tar.gz'), 2048, 10)

        call_command('backup', type='manual')

        self.assertTrue(Backup.objects.exists())
        backup = Backup.objects.first()
        self.assertEqual(backup.status, 'success')
        self.assertEqual(backup.backup_type, 'manual')
        self.assertEqual(backup.database_size_bytes, 1024)

    @patch('django.core.management.call_command')
    def test_scheduled_backup_logic(self, mock_call_command):
        """Test the schedule checking logic."""
        pass

    @patch('backup.management.commands.run_scheduled_backup.call_command')
    def test_run_scheduled_backup_needed(self, mock_run):
        """Test that it runs when a backup is missing."""
        # Set timezone to Chicago
        pref = Preference.objects.get(key='loc_timezone')
        pref.value = 'America/Chicago'
        pref.save()
        
        # Schedule is 02:00. 
        # In Chicago, 03:00 is well past 02:00.
        # Set NOW to 03:00 Chicago Time.
        chi_tz = zoneinfo.ZoneInfo('America/Chicago')
        now_chi = datetime.now(chi_tz).replace(hour=3, minute=0, second=0, microsecond=0)
        
        with patch('django.utils.timezone.now', return_value=now_chi.astimezone(dt_timezone.utc)):
            from backup.management.commands.run_scheduled_backup import Command
            cmd = Command()
            cmd.stdout = MagicMock()
            cmd.handle()
            
            mock_run.assert_called_with('backup', type='scheduled')

    @patch('backup.management.commands.run_scheduled_backup.call_command')
    def test_run_scheduled_backup_not_needed(self, mock_run):
        """Test that it skips when a backup exists."""
        # Set timezone to Chicago
        pref = Preference.objects.get(key='loc_timezone')
        pref.value = 'America/Chicago'
        pref.save()
        
        # Schedule is 02:00.
        # Backup exists at 02:30 Chicago Time.
        chi_tz = zoneinfo.ZoneInfo('America/Chicago')
        now_chi = datetime.now(chi_tz).replace(hour=3, minute=0, second=0, microsecond=0)
        backup_start_chi = now_chi.replace(hour=2, minute=30)
        
        # Create existing backup
        Backup.objects.create(
            backup_id='test_backup_done',
            backup_path='/tmp',
            status='success',
            backup_type='scheduled',
            start_time=backup_start_chi.astimezone(dt_timezone.utc),
            created_by=self.user,
            updated_by=self.user
        )
        
        with patch('django.utils.timezone.now', return_value=now_chi.astimezone(dt_timezone.utc)):
            from backup.management.commands.run_scheduled_backup import Command
            cmd = Command()
            cmd.stdout = MagicMock()
            cmd.handle()
            
            mock_run.assert_not_called()

    @patch('backup.management.commands.start_backup_scheduler.call_command')
    @patch('backup.management.commands.start_backup_scheduler.time.sleep')
    def test_scheduler_daemon(self, mock_sleep, mock_call):
        """Test that the daemon calls the checker."""
        # We need to break the infinite loop
        mock_sleep.side_effect = KeyboardInterrupt
        
        from backup.management.commands.start_backup_scheduler import Command
        cmd = Command()
        cmd.stdout = MagicMock()
        
        try:
            cmd.handle()
        except KeyboardInterrupt:
            pass
        except SystemExit:
            pass
            
        mock_call.assert_called_with('run_scheduled_backup')
