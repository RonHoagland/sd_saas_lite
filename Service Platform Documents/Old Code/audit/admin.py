"""
Audit Admin - Read-only admin interface for sessions and event logging
"""

from django.contrib import admin
from .models import Session, UserTransaction


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'attempted_username', 'auth_result', 'started_at', 'ended_at', 'ip_address')
    list_filter = ('auth_result', 'end_reason', 'started_at')
    search_fields = ('user__username', 'attempted_username', 'ip_address')
    readonly_fields = ('id', 'user', 'attempted_username', 'auth_result', 'auth_failure_reason', 
                      'started_at', 'ended_at', 'end_reason', 'client_info', 'ip_address', 'user_snapshot')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserTransaction)
class UserTransactionAdmin(admin.ModelAdmin):
    list_display = ('event_ts', 'event_type', 'entity_type', 'entity_id', 'user', 'summary')
    list_filter = ('event_type', 'entity_type', 'event_ts')
    search_fields = ('entity_type', 'entity_id', 'user__username', 'summary')
    readonly_fields = ('id', 'session', 'user', 'event_ts', 'event_type', 
                      'entity_type', 'entity_id', 'reason_text', 'summary')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
