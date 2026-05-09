# workforce/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from workforce.models import WorkGroup, WorkGroupTeam, WGTRole, WGDivision, WorkGroupAsset, Skill, EmployeeSkill


@admin.register(WGDivision)
class WGDivisionAdmin(TenantModelAdmin):
    list_display = ('name', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkGroup)
class WorkGroupAdmin(TenantModelAdmin):
    list_display = ('name', 'division', 'status', 'manager', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WGTRole)
class WGTRoleAdmin(TenantModelAdmin):
    list_display = ('name', 'work_group', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('name', 'work_group__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkGroupTeam)
class WorkGroupTeamAdmin(TenantModelAdmin):
    list_display = ('work_group', 'user', 'role', 'is_lead', 'tenant_id')
    list_filter = ('tenant_id', 'is_lead')
    search_fields = ('work_group__name', 'user__email')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(WorkGroupAsset)
class WorkGroupAssetAdmin(TenantModelAdmin):
    list_display = ('work_group', 'asset', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('work_group__name', 'asset__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Skill)
class SkillAdmin(TenantModelAdmin):
    list_display = ('name', 'category', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'category')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(EmployeeSkill)
class EmployeeSkillAdmin(TenantModelAdmin):
    list_display = ('employee', 'skill', 'date_earned', 'expiration_date', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('employee__email', 'skill__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
