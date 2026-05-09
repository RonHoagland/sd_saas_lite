"""
Management command to run the backup scheduler as a long-running process.

This acts as a simple daemon that checks the schedule every minute.
"""

import time
import sys
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections

class Command(BaseCommand):
    help = 'Run the backup scheduler daemon'


    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting backup scheduler daemon...'))
        self.stdout.write('Press Ctrl+C to stop.')
        
        from django.conf import settings
        from pathlib import Path
        heartbeat_file = Path(settings.BASE_DIR) / 'scheduler_heartbeat.log'

        try:
            while True:
                # Close DB connections to prevent timeouts/stale connections in long-running process
                for conn in connections.all():
                    conn.close_if_unusable_or_obsolete()
                
                try:
                    # Write heartbeat
                    with open(heartbeat_file, 'w') as f:
                        f.write(f"Running: {time.ctime()}\n")
                    
                    # Run the check
                    call_command('run_scheduled_backup')
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error checking schedule: {e}"))
                    with open(heartbeat_file, 'a') as f:
                        f.write(f"Error: {e}\n")

                # Wait for next minute
                time.sleep(60)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping backup scheduler...'))
            if heartbeat_file.exists():
                heartbeat_file.unlink()
            sys.exit(0)
        except BaseException as e:
            self.stdout.write(self.style.ERROR(f"Fatal error: {e}"))
            sys.exit(1)
