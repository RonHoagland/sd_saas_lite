"""
Management command to check and trigger scheduled backups.

This command is designed to be run periodically (e.g., via cron every 15 minutes).
It checks the configured backup schedule and runs a backup if:
1. Backups are enabled globally.
2. The current time is past the scheduled time for today (or yesterday if today's hasn't happened yet).
3. No 'scheduled' backup has successfully completed or started since that target time.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.management import call_command
from backup.models import Backup, BackupSettings

class Command(BaseCommand):
    help = 'Check schedule and trigger backup if due'

    def handle(self, *args, **options):
        # 1. Get Settings
        try:
            settings_obj = BackupSettings.get_settings()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to load settings: {e}"))
            return

        if not settings_obj.is_enabled:
            self.stdout.write("Backups are disabled in settings.")
            return

        # 2. Determine Target Run Time
        # We need to respect the User's Configured Timezone (loc_timezone)
        try:
            from core.models import Preference
            import zoneinfo
            
            pref = Preference.objects.filter(key='l10n_timezone').first()
            if pref and pref.value:
                user_tz = zoneinfo.ZoneInfo(pref.value)
                tz_source = f"Preference ({pref.value})"
            else:
                user_tz = zoneinfo.ZoneInfo('America/Chicago')
                tz_source = "Default (America/Chicago)"
        except Exception as e:
            user_tz = dt_timezone.utc
            tz_source = f"Fallback (UTC) - Error: {e}"

        now_utc = timezone.now()
        now_user = now_utc.astimezone(user_tz)
        schedule_time = settings_obj.schedule_time
        
        # Construct target for today in USER TIME
        # This ensures that "02:00" means "02:00 Chicago Time" (or whatever user set)
        naive_target = datetime.combine(now_user.date(), schedule_time)
        try:
            today_target_user = timezone.make_aware(naive_target, timezone=user_tz)
        except Exception:
            # Fallback for ambiguous DST times, strict=False is default in newer Django? 
            # Or use explicit call
            today_target_user = now_user.replace(
                hour=schedule_time.hour, 
                minute=schedule_time.minute, 
                second=schedule_time.second, 
                microsecond=0
            )

        # Convert back to UTC for reliable comparison
        today_target_utc = today_target_user.astimezone(dt_timezone.utc)

        if now_utc >= today_target_utc:
            # We are past the schedule time today
            target_run_time_utc = today_target_utc
        else:
            # We are before the schedule time today, look for yesterday's run
            target_run_time_utc = today_target_utc - timedelta(days=1)

        self.stdout.write(f"Checking schedule...")
        self.stdout.write(f"  Timezone:        {tz_source}")
        self.stdout.write(f"  Current (UTC):   {now_utc}")
        self.stdout.write(f"  Current (User):  {now_user}")
        # 3. Check for existing runs
        # We look for any scheduled backup that started *after* the target run time.
        existing = Backup.objects.filter(
            backup_type='scheduled',
            start_time__gte=target_run_time_utc,
            status__in=['success', 'in_progress']
        ).order_by('-start_time').first()

        if existing:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Scheduled backup already covered. (Backup ID: {existing.backup_id}, Status: {existing.status})"
            ))
            return

        # 4. Check concurrency (optional but good practice)
        # Verify no other backup is currently running to avoid resource contention
        if Backup.objects.filter(status='in_progress').exists():
            self.stdout.write(self.style.WARNING(
                "Another backup is currently in progress. Skipping this schedule check."
            ))
            return

        # 5. Trigger Backup
        self.stdout.write(self.style.WARNING(
            f"⚠ No backup found since {target_run_time_utc}. Triggering scheduled backup now..."
        ))
        
        try:
            call_command('backup', type='scheduled')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to trigger backup: {e}"))
