# lifecycle/admin.py
# Django admin integration for Lifecycle Framework models.
# Source: Lifecycle Framework Specification V1, Section 5.

from django.contrib import admin
from staff.admin import TenantModelAdmin
from lifecycle.models import (
    LifecycleStateDef,
    LifecycleTransitionRule,
    LifecycleTransitionAudit
)


@admin.register(LifecycleStateDef)
class LifecycleStateDefAdmin(TenantModelAdmin):
    list_display = (
        'entity_type',
        'state_name',
        'state_label',
        'state_type',
        'is_default',
        'sort_order',
        'tenant_id'
    )
    list_filter = ('tenant_id', 'entity_type', 'state_type', 'is_default')
    search_fields = ('entity_type', 'state_name', 'state_label')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
    ordering = ('entity_type', 'sort_order')


@admin.register(LifecycleTransitionRule)
class LifecycleTransitionRuleAdmin(TenantModelAdmin):
    list_display = (
        'entity_type',
        'transition_display',
        'required_role',
        'requires_reason',
        'is_admin_override',
        'tenant_id'
    )
    list_filter = ('tenant_id', 'entity_type', 'requires_reason', 'is_admin_override')
    search_fields = ('entity_type', 'from_state', 'to_state', 'required_role')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
    ordering = ('entity_type', 'from_state', 'to_state')

    def transition_display(self, obj):
        """Display transition as 'from_state → to_state'"""
        return f'{obj.from_state} → {obj.to_state}'
    transition_display.short_description = 'Transition'


@admin.register(LifecycleTransitionAudit)
class LifecycleTransitionAuditAdmin(admin.ModelAdmin):
    """
    Read-only view of transition audit records.
    No add/change/delete permissions via Django admin.
    """
    list_display = (
        'entity_type',
        'entity_id',
        'transition_display',
        'user_display',
        'timestamp',
        'is_override',
    )
    list_filter = ('tenant_id', 'entity_type', 'timestamp', 'is_override')
    search_fields = ('entity_type', 'entity_id', 'user_display')
    readonly_fields = (
        'id',
        'tenant_id',
        'timestamp',
        'user_id',
        'user_display',
        'entity_type',
        'entity_id',
        'from_state',
        'to_state',
        'reason',
        'is_override',
        'ip_address',
    )
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def transition_display(self, obj):
        """Display transition as 'from_state → to_state'"""
        return f'{obj.from_state} → {obj.to_state}'
    transition_display.short_description = 'Transition'
