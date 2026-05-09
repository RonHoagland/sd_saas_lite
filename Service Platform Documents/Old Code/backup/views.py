from django.shortcuts import render, redirect
from pathlib import Path
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.management import call_command
from .models import Backup, BackupSettings
from core.utils import apply_sorting

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def backup_dashboard_view(request):
    settings = BackupSettings.get_settings()
    backups = Backup.objects.all()
    
    # Sorting
    backups, sort_field, sort_dir = apply_sorting(
        backups, 
        request, 
        allowed_fields=['backup_timestamp', 'backup_id', 'status', 'backup_type', 'database_size_bytes'], 
        default_sort='backup_timestamp', 
        default_dir='desc'
    )

    return render(request, "backup/dashboard.html", {
        "settings": settings,
        "backups": backups,
        "current_sort": sort_field,
        "current_dir": sort_dir
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def trigger_backup_view(request):
    if request.method == "POST":
        try:
            # Note: This is synchronous and might block
            call_command('backup', type='manual')
            messages.success(request, "Backup completed successfully.")
        except Exception as e:
            messages.error(request, f"Backup failed: {str(e)}")
            
    return redirect('backup_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def restore_backup_view(request, backup_id):
    if request.method == "POST":
        try:
            # Force close connections before heavy DB operation to avoid locks
            from django.db import connections
            connections.close_all()
            
            # Call restore command non-interactively
            # Note: This effectively replaces the DB, so the request might fail to write session 
            # if done synchronously, but we attempt it anyway as requested.
            call_command('restore', backup_id, force=True)
            messages.success(request, f"Restore of {backup_id} initiated successfully. Please log in again if session was invalidated.")
        except Exception as e:
            messages.error(request, f"Restore failed: {str(e)}")
            
    return redirect('backup_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_backup_view(request, backup_id):
    if request.method == "POST":
        try:
            backup = Backup.objects.get(backup_id=backup_id)
            path = Path(backup.backup_path)
            
            # Delete physical files
            if path.exists() and path.is_dir():
                import shutil
                shutil.rmtree(path)
            
            # Delete record
            backup.delete()
            messages.success(request, f"Backup {backup_id} deleted successfully.")
            
        except Backup.DoesNotExist:
            messages.error(request, f"Backup {backup_id} not found.")
        except Exception as e:
            messages.error(request, f"Failed to delete backup: {str(e)}")
            
    return redirect('backup_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_settings_view(request):
    if request.method == "POST":
        settings = BackupSettings.get_settings()
        
        # 1. Schedule Time
        if 'schedule_time' in request.POST:
            time_str = request.POST.get('schedule_time')
            try:
                # Basic validation, model will do full clean
                settings.schedule_time = time_str
                settings.save()
                messages.success(request, "Backup schedule updated.")
            except Exception as e:
                messages.error(request, f"Invalid time format: {str(e)}")

        # 2. Retention Count
        elif 'retention_count' in request.POST:
            try:
                count = int(request.POST.get('retention_count'))
                if count < 5:
                    raise ValueError("Retention must be at least 5.")
                settings.retention_count = count
                settings.save()
                messages.success(request, "Retention policy updated.")
            except ValueError as e:
                messages.error(request, str(e))

        # 3. Enable/Disable
        elif 'is_enabled' in request.POST:
            val = request.POST.get('is_enabled') == 'true'
            settings.is_enabled = val
            settings.save()
            status = "enabled" if val else "disabled"
            messages.success(request, f"Automatic backups {status}.")

    return redirect('backup_dashboard')
