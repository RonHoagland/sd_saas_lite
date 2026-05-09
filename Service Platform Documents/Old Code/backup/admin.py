from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import BackupSettings, Backup, BackupLog
import zoneinfo
from datetime import timezone as dt_timezone

# Common Mixin for Local Time Display
class LocalTimeMixin:
    """
    Mixin to display datetimes in the user's configured 'loc_timezone'.
    """
    def _format_local_time(self, dt):
        if not dt:
            return "—"
        try:
            from core.models import Preference
            
            # Default to UTC
            tz = dt_timezone.utc
            
            # Try to get preference (Naive caching could be added here if perf becomes an issue)
            # For Admin UI, N+1 is usually acceptable for small record sets.
            pref = Preference.objects.filter(key='loc_timezone').first()
            if pref and pref.value:
                try:
                    tz = zoneinfo.ZoneInfo(pref.value)
                except Exception:
                    pass
            
            # Convert
            local_dt = dt.astimezone(tz)
            return local_dt.strftime('%Y-%m-%d %I:%M:%S %p (%Z)')
        except Exception:
            return dt

    def local_created_at(self, obj):
        return self._format_local_time(obj.created_at)
    local_created_at.short_description = "Created At"
    local_created_at.admin_order_field = 'created_at'

    def local_updated_at(self, obj):
        return self._format_local_time(obj.updated_at)
    local_updated_at.short_description = "Updated At"
    local_updated_at.admin_order_field = 'updated_at'


@admin.register(BackupSettings)
class BackupSettingsAdmin(LocalTimeMixin, admin.ModelAdmin):
    fields = [
        'backup_path',
        'schedule_time',
        'retention_count',
        'is_enabled',
        'local_created_at',
        'local_updated_at',
    ]
    readonly_fields = ['local_created_at', 'local_updated_at']
    
    def has_add_permission(self, request):
        """Only allow one settings instance."""
        return not BackupSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Never allow deletion of settings."""
        return False


@admin.register(Backup)
class BackupAdmin(LocalTimeMixin, admin.ModelAdmin):
    list_display = [
        'backup_id',
        'local_backup_timestamp',
        'status_badge',
        'backup_type',
        'database_size_display',
        'file_count',
        'duration',
    ]
    list_filter = ['status', 'backup_type', 'backup_timestamp']
    search_fields = ['backup_id', 'backup_path']
    readonly_fields = [
        'backup_id',
        'backup_path',
        'local_backup_timestamp',
        'local_start_time',
        'local_end_time',
        'database_size_bytes',
        'files_size_bytes',
        'file_count',
        'app_version',
        'schema_version',
        'database_version',
        'local_created_at',
        'local_updated_at',
    ]
    
    fieldsets = (
        ('Backup Identity', {
            'fields': ('backup_id', 'backup_path', 'status', 'backup_type')
        }),
        ('Timing', {
            'fields': ('local_backup_timestamp', 'local_start_time', 'local_end_time')
        }),
        ('Versions', {
            'fields': ('app_version', 'schema_version', 'database_version', 'install_mode')
        }),
        ('Content', {
            'fields': ('database_size_bytes', 'files_size_bytes', 'file_count')
        }),
        ('Failure Details', {
            'fields': ('failure_reason',)
        }),
        ('Audit', {
            'fields': ('created_by', 'local_created_at', 'updated_by', 'local_updated_at')
        }),
    )
    
    def local_backup_timestamp(self, obj):
        return self._format_local_time(obj.backup_timestamp)
    local_backup_timestamp.short_description = 'Backup Timestamp'
    local_backup_timestamp.admin_order_field = 'backup_timestamp'

    def local_start_time(self, obj):
        return self._format_local_time(obj.start_time)
    local_start_time.short_description = 'Start Time'
    local_start_time.admin_order_field = 'start_time'

    def local_end_time(self, obj):
        return self._format_local_time(obj.end_time)
    local_end_time.short_description = 'End Time'
    local_end_time.admin_order_field = 'end_time'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'success': '#28a745',
            'failed': '#dc3545',
            'in_progress': '#ffc107',
            'partial': '#fd7e14',
            'pending': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def database_size_display(self, obj):
        """Format database size in MB."""
        if obj.database_size_bytes:
            mb = obj.database_size_bytes / (1024 * 1024)
            return f"{mb:.2f} MB"
        return "—"
    database_size_display.short_description = 'DB Size'
    
    def duration(self, obj):
        """Display backup duration."""
        seconds = obj.duration_seconds()
        if seconds:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        return "—"
    duration.short_description = 'Duration'
    
    def has_add_permission(self, request):
        """Backups created programmatically, not via admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent accidental backup deletion."""
        return False


@admin.register(BackupLog)
class BackupLogAdmin(LocalTimeMixin, admin.ModelAdmin):
    list_display = [
        'local_log_timestamp',
        'operation_display',
        'status_badge',
        'backup_id_link',
        'initiated_by',
    ]
    list_filter = ['operation', 'status', 'log_timestamp']
    search_fields = ['message', 'initiated_by', 'backup__backup_id']
    readonly_fields = [
        'backup',
        'operation',
        'status',
        'message',
        'local_log_timestamp',
        'duration_seconds',
        'initiated_by',
        'local_created_at',
        'local_updated_at',
    ]
    
    fieldsets = (
        ('Operation', {
            'fields': ('operation', 'status', 'backup')
        }),
        ('Details', {
            'fields': ('message', 'duration_seconds')
        }),
        ('Metadata', {
            'fields': ('initiated_by', 'local_log_timestamp')
        }),
        ('Audit', {
            'fields': ('created_by', 'local_created_at', 'updated_by', 'local_updated_at')
        }),
    )
    
    def local_log_timestamp(self, obj):
        return self._format_local_time(obj.log_timestamp)
    local_log_timestamp.short_description = 'Log Timestamp'
    local_log_timestamp.admin_order_field = 'log_timestamp'

    def operation_display(self, obj):
        """Display operation type."""
        return obj.get_operation_display()
    operation_display.short_description = 'Operation'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def backup_id_link(self, obj):
        """Link to backup if available."""
        if obj.backup:
            url = f'/admin/backup/backup/{obj.backup.id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.backup.backup_id)
        return "—"
    backup_id_link.short_description = 'Backup'
    
    def has_add_permission(self, request):
        """Logs created programmatically."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent log deletion."""
        return False
