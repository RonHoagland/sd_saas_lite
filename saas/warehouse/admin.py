# warehouse/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from warehouse.models import (
    Warehouse, SubLocation, LocationAssignedInventory,
    InventoryCount, InventoryTransfer, Location,
)


@admin.register(Warehouse)
class WarehouseAdmin(TenantModelAdmin):
    list_display = ('warehouse_number', 'name', 'type', 'status',
                    'assigned_user', 'tenant_id')
    list_filter = ('tenant_id', 'type', 'status')
    search_fields = ('warehouse_number', 'name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(SubLocation)
class SubLocationAdmin(TenantModelAdmin):
    list_display = ('location_number', 'warehouse', 'location_type', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('location_number', 'warehouse__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(LocationAssignedInventory)
class LocationAssignedInventoryAdmin(TenantModelAdmin):
    list_display = ('product', 'sub_location', 'quantity_on_hand', 'serial_number', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('product__name', 'product__product_number', 'serial_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(InventoryCount)
class InventoryCountAdmin(TenantModelAdmin):
    list_display = ('product', 'count_date', 'counted_by', 'physical_count',
                    'system_count', 'variance', 'adjustment_applied', 'tenant_id')
    list_filter = ('tenant_id', 'adjustment_applied')
    search_fields = ('product__name', 'product__product_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(InventoryTransfer)
class InventoryTransferAdmin(TenantModelAdmin):
    list_display = ('product', 'source_location', 'dest_location',
                    'quantity', 'transfer_date', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('product__name', 'product__product_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Location)
class LocationAdmin(TenantModelAdmin):
    list_display = ('name', 'department', 'warehouse', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('name', 'department__name', 'warehouse__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
