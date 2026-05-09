# fleet/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from fleet.models import Vehicle, VehicleMaintenance, MileageLog, VehicleInventory


@admin.register(Vehicle)
class VehicleAdmin(TenantModelAdmin):
    list_display = ('vehicle_number', 'name', 'vehicle_type', 'status',
                    'make', 'model', 'year', 'license_plate',
                    'assigned_to', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'vehicle_type')
    search_fields = ('vehicle_number', 'name', 'vin', 'license_plate')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(VehicleMaintenance)
class VehicleMaintenanceAdmin(TenantModelAdmin):
    list_display = ('vehicle', 'service_type', 'status', 'service_date',
                    'next_service_date', 'cost', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('vehicle__name', 'service_type')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(MileageLog)
class MileageLogAdmin(TenantModelAdmin):
    list_display = ('vehicle', 'log_date', 'driver', 'odometer_start',
                    'odometer_end', 'miles_driven', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('vehicle__name', 'vehicle__vehicle_number', 'purpose')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(VehicleInventory)
class VehicleInventoryAdmin(TenantModelAdmin):
    list_display = ('vehicle', 'product', 'quantity_on_hand', 'reorder_point', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('vehicle__name', 'product__name', 'product__product_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
