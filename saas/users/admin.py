# users/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from users.models import (
    User, Department, Position, Role, EmployeeRole, EmployeePosition,
    RolePermission, TenantPreference, EmployeePreference,
    SessionLog, LoginAttemptLog, EmployeeZone,
)


@admin.register(User)
class UserAdmin(TenantModelAdmin):
    list_display = ('email', 'tenant_id', 'status', 'employee_number',
                    'mfa_enabled', 'created_on')
    list_filter = ('tenant_id', 'status', 'mfa_enabled', 'mfa_exempt')
    search_fields = ('email', 'employee_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on',
                       'failed_login_count')


@admin.register(Department)
class DepartmentAdmin(TenantModelAdmin):
    list_display = ('name', 'tenant_id', 'status')
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(TenantModelAdmin):
    list_display = ('title', 'department', 'tenant_id', 'status')
    search_fields = ('title',)


@admin.register(Role)
class RoleAdmin(TenantModelAdmin):
    list_display = ('name', 'tenant_id', 'is_custom')
    list_filter = ('tenant_id', 'is_custom')
    search_fields = ('name',)


@admin.register(EmployeeRole)
class EmployeeRoleAdmin(TenantModelAdmin):
    list_display = ('employee', 'role', 'tenant_id')
    list_filter = ('tenant_id',)


@admin.register(EmployeePosition)
class EmployeePositionAdmin(TenantModelAdmin):
    list_display = ('employee', 'position', 'is_primary', 'tenant_id')


@admin.register(RolePermission)
class RolePermissionAdmin(TenantModelAdmin):
    list_display = ('role', 'resource_key', 'can_create', 'can_view',
                    'can_edit', 'can_delete', 'tenant_id')
    list_filter = ('tenant_id', 'resource_key')
    search_fields = ('resource_key',)


@admin.register(TenantPreference)
class TenantPreferenceAdmin(TenantModelAdmin):
    list_display = ('company_name', 'tenant_id', 'default_currency', 'timezone')
    search_fields = ('company_name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(EmployeePreference)
class EmployeePreferenceAdmin(TenantModelAdmin):
    list_display = ('user', 'ui_theme', 'tenant_id')


@admin.register(SessionLog)
class SessionLogAdmin(TenantModelAdmin):
    list_display = ('id', 'tier_at_login', 'user', 'tenant_id', 'login_at',
                    'logout_at', 'mfa_used', 'device_type')
    list_filter = ('tenant_id', 'tier_at_login', 'mfa_used', 'device_type')
    search_fields = ('id',)
    readonly_fields = ('id', 'tenant_id', 'tier_at_login', 'created_on', 'updated_on',
                       'login_at')


@admin.register(LoginAttemptLog)
class LoginAttemptLogAdmin(TenantModelAdmin):
    list_display = ('user_email', 'tenant_id', 'success', 'failure_reason',
                    'ip_address', 'attempted_at')
    list_filter = ('tenant_id', 'success', 'failure_reason')
    search_fields = ('user_email', 'ip_address')
    readonly_fields = ('id', 'tenant_id', 'attempted_at')


@admin.register(EmployeeZone)
class EmployeeZoneAdmin(TenantModelAdmin):
    list_display = ('employee', 'zone', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('employee__email', 'zone__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
