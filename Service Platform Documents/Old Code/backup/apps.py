from django.apps import AppConfig


class BackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backup'
    verbose_name = 'Backup & Restore Infrastructure'

    def ready(self):
        """
        Initialize the backup scheduler when running as a server.
        """
        import sys
        import os
        from threading import Thread
        from django.core.management import call_command
        
        # Check if we are running as a server (to avoid starting in migrate, shell, etc.)
        # Supports 'runserver' and 'runserver_plus'
        is_server = any(arg.startswith('runserver') for arg in sys.argv)
        
        # Check for auto-reloader to avoid double-starting
        # RUN_MAIN is set by Django's auto-reloader in the worker process
        # WERKZEUG_RUN_MAIN is set by runserver_plus / Werkzeug
        is_reloader = os.environ.get('RUN_MAIN') == 'true' or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        no_reload = '--noreload' in sys.argv
        
        # Start only if:
        # 1. It is 'runserver' AND we are in the reloader worker (RUN_MAIN=true)
        # OR
        # 2. It is 'runserver' with --noreload (RUN_MAIN not set)
        if is_server and (is_reloader or no_reload):
            def start_scheduler_thread():
                try:
                    # Run the existing daemon command
                    # It handles its own infinite loop and error catching
                    call_command('start_backup_scheduler')
                except Exception as e:
                    print(f"Failed to auto-start backup scheduler: {e}")

            # Daemon thread ensures it dies when the main process does
            thread = Thread(target=start_scheduler_thread, daemon=True, name="BackupScheduler")
            thread.start()
            print("Backup Scheduler started in background thread.")
