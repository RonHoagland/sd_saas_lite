# numbering/admin.py
# Django admin registration for numbering models.
# Source: Numbering Service Specification V1, Section 5.

from django.contrib import admin
from staff.admin import TenantModelAdmin
from .models import NumberingRule, NumberSequence, AssignedNumber


@admin.register(NumberingRule)
class NumberingRuleAdmin(TenantModelAdmin):
    """
    Admin for NumberingRule.
    Allows staff to view, create, and edit numbering rules per tenant.
    """

    list_display = (
        'entity_type',
        'prefix',
        'is_enabled',
        'include_year',
        'reset_behavior',
        'tenant_id',
    )
    list_filter = ('tenant_id', 'is_enabled', 'reset_behavior')
    search_fields = ('entity_type', 'prefix', 'description')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on', 'created_by', 'updated_by')

    fieldsets = (
        ('Entity & Status', {
            'fields': ('entity_type', 'is_enabled'),
        }),
        ('Format', {
            'fields': (
                'prefix',
                'include_year',
                'year_format',
                'include_month',
                'sequence_length',
                'delimiter',
            ),
        }),
        ('Reset Behavior', {
            'fields': ('reset_behavior',),
        }),
        ('Description', {
            'fields': ('description',),
        }),
        ('Audit', {
            'fields': ('id', 'tenant_id', 'created_by', 'created_on', 'updated_by', 'updated_on'),
            'classes': ('collapse',),
        }),
    )


@admin.register(NumberSequence)
class NumberSequenceAdmin(TenantModelAdmin):
    """
    Read-only admin for NumberSequence.
    Staff can view sequence state but cannot modify it directly.
    """

    list_display = ('rule', 'current_value', 'last_reset_date')
    list_filter = ('last_reset_date',)
    search_fields = ('rule__entity_type',)
    readonly_fields = ('id', 'rule', 'current_value', 'last_reset_date')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AssignedNumber)
class AssignedNumberAdmin(TenantModelAdmin):
    """
    Read-only admin for AssignedNumber.
    These records are immutable and cannot be modified or deleted.
    """

    list_display = (
        'number',
        'entity_type',
        'entity_id',
        'assigned_at',
        'assigned_by',
        'tenant_id',
    )
    list_filter = ('tenant_id', 'entity_type', 'assigned_at')
    search_fields = ('number', 'entity_type', 'entity_id')
    readonly_fields = (
        'id',
        'tenant_id',
        'rule',
        'entity_type',
        'entity_id',
        'number',
        'assigned_at',
        'assigned_by',
        'created_by',
        'created_on',
        'updated_by',
        'updated_on',
    )

    fieldsets = (
        ('Assignment', {
            'fields': ('number', 'entity_type', 'entity_id', 'assigned_by', 'rule'),
        }),
        ('Audit', {
            'fields': (
                'id',
                'tenant_id',
                'assigned_at',
                'created_by',
                'created_on',
                'updated_by',
                'updated_on',
            ),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
