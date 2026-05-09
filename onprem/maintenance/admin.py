# maintenance/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from maintenance.models import (
    Asset, SubAsset, Agreement, CustomerAgreement, PreventativeMaintenance,
)


@admin.register(Asset)
class AssetAdmin(TenantModelAdmin):
    list_display = ('asset_number', 'name', 'customer', 'status',
                    'manufacturer', 'model_number', 'serial_number', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('asset_number', 'name', 'serial_number', 'customer__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(SubAsset)
class SubAssetAdmin(TenantModelAdmin):
    list_display = ('name', 'asset', 'status', 'manufacturer',
                    'model_number', 'serial_number', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name', 'serial_number', 'asset__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Agreement)
class AgreementAdmin(TenantModelAdmin):
    list_display = ('name', 'status', 'default_duration_months', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('name',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(CustomerAgreement)
class CustomerAgreementAdmin(TenantModelAdmin):
    list_display = ('agreement', 'customer', 'status', 'start_date',
                    'end_date', 'auto_renew', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'auto_renew')
    search_fields = ('customer__name', 'agreement__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(PreventativeMaintenance)
class PreventativeMaintenanceAdmin(TenantModelAdmin):
    list_display = ('task_name', 'asset', 'frequency', 'status',
                    'last_performed_date', 'next_due_date', 'assigned_to', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'frequency')
    search_fields = ('task_name', 'asset__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
