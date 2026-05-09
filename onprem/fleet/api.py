# fleet/api.py
# REST API serializers and viewsets for fleet app models.
#
# Models:
#   Vehicle, VehicleMaintenance, MileageLog, VehicleInventory

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import Vehicle, VehicleMaintenance, MileageLog, VehicleInventory


# ─── Vehicle ──────────────────────────────────────────────────────────────────

class VehicleSerializer(TenantModelSerializer):
    assigned_to_display = serializers.CharField(source='assigned_to.email', read_only=True)
    assigned_work_group_display = serializers.CharField(source='assigned_work_group.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = TenantModelSerializer.Meta.fields + [
            'vehicle_number',
            'name',
            'vehicle_type',
            'status',
            'make',
            'model',
            'year',
            'vin',
            'license_plate',
            'color',
            'assigned_to',
            'assigned_to_display',
            'assigned_work_group',
            'assigned_work_group_display',
            'registration_expiry',
            'insurance_expiry',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'vehicle_number',
            'assigned_to_display',
            'assigned_work_group_display',
        ]


class VehicleViewSet(TenantModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    filterset_fields = ['vehicle_type', 'status', 'assigned_to_id', 'assigned_work_group_id']
    search_fields = ['name', 'vehicle_number', 'vin', 'license_plate', 'make', 'model']
    ordering_fields = ['name', 'vehicle_number', 'created_on', 'status']


# ─── VehicleMaintenance ───────────────────────────────────────────────────────

class VehicleMaintenanceSerializer(TenantModelSerializer):
    vehicle_display = serializers.CharField(source='vehicle.name', read_only=True)

    class Meta:
        model = VehicleMaintenance
        fields = TenantModelSerializer.Meta.fields + [
            'vehicle',
            'vehicle_display',
            'service_type',
            'status',
            'service_date',
            'next_service_date',
            'mileage_at_service',
            'next_service_mileage',
            'performed_by',
            'cost',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'vehicle_display',
        ]


class VehicleMaintenanceViewSet(TenantModelViewSet):
    queryset = VehicleMaintenance.objects.all()
    serializer_class = VehicleMaintenanceSerializer
    filterset_fields = ['vehicle_id', 'status', 'service_date']
    search_fields = ['service_type', 'vehicle__name']
    ordering_fields = ['service_date', 'next_service_date', 'created_on', 'status']


# ─── MileageLog ───────────────────────────────────────────────────────────────

class MileageLogSerializer(TenantModelSerializer):
    vehicle_display = serializers.CharField(source='vehicle.name', read_only=True)
    driver_display = serializers.CharField(source='driver.email', read_only=True)
    work_order_display = serializers.CharField(source='work_order.id', read_only=True)

    class Meta:
        model = MileageLog
        fields = TenantModelSerializer.Meta.fields + [
            'vehicle',
            'vehicle_display',
            'log_date',
            'odometer_start',
            'odometer_end',
            'miles_driven',
            'driver',
            'driver_display',
            'purpose',
            'notes',
            'work_order',
            'work_order_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'vehicle_display',
            'driver_display',
            'work_order_display',
        ]


class MileageLogViewSet(TenantModelViewSet):
    queryset = MileageLog.objects.all()
    serializer_class = MileageLogSerializer
    filterset_fields = ['vehicle_id', 'driver_id', 'log_date']
    search_fields = ['vehicle__name', 'purpose']
    ordering_fields = ['log_date', 'created_on']


# ─── VehicleInventory ────────────────────────────────────────────────────────

class VehicleInventorySerializer(TenantModelSerializer):
    vehicle_display = serializers.CharField(source='vehicle.name', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = VehicleInventory
        fields = TenantModelSerializer.Meta.fields + [
            'vehicle',
            'vehicle_display',
            'product',
            'product_display',
            'quantity_on_hand',
            'reorder_point',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'vehicle_display',
            'product_display',
        ]


class VehicleInventoryViewSet(TenantModelViewSet):
    queryset = VehicleInventory.objects.all()
    serializer_class = VehicleInventorySerializer
    filterset_fields = ['vehicle_id', 'product_id']
    search_fields = ['vehicle__name', 'product__name']
    ordering_fields = ['quantity_on_hand', 'created_on']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'vehicle-maintenance', VehicleMaintenanceViewSet, basename='vehicle-maintenance')
router.register(r'mileage-logs', MileageLogViewSet, basename='mileage-log')
router.register(r'vehicle-inventory', VehicleInventoryViewSet, basename='vehicle-inventory')
