# warehouse/api.py
# REST API serializers and viewsets for warehouse app models.
#
# Models:
#   Warehouse, SubLocation, LocationAssignedInventory, InventoryCount,
#   InventoryTransfer, Location

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import (
    Warehouse, SubLocation, LocationAssignedInventory, InventoryCount,
    InventoryTransfer, Location
)


# ─── Warehouse ────────────────────────────────────────────────────────────────

class WarehouseSerializer(TenantModelSerializer):
    assigned_user_display = serializers.CharField(source='assigned_user.email', read_only=True)

    class Meta:
        model = Warehouse
        fields = TenantModelSerializer.Meta.fields + [
            'warehouse_number',
            'name',
            'type',
            'status',
            'assigned_user',
            'assigned_user_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'warehouse_number',
            'assigned_user_display',
        ]


class WarehouseViewSet(TenantModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    filterset_fields = ['type', 'status', 'assigned_user_id']
    search_fields = ['name', 'warehouse_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── SubLocation ──────────────────────────────────────────────────────────────

class SubLocationSerializer(TenantModelSerializer):
    warehouse_display = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = SubLocation
        fields = TenantModelSerializer.Meta.fields + [
            'warehouse',
            'warehouse_display',
            'location_number',
            'location_type',
            'description',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'warehouse_display',
        ]


class SubLocationViewSet(TenantModelViewSet):
    queryset = SubLocation.objects.all()
    serializer_class = SubLocationSerializer
    filterset_fields = ['warehouse_id', 'status']
    search_fields = ['location_number', 'warehouse__name']
    ordering_fields = ['location_number', 'created_on', 'status']


# ─── LocationAssignedInventory ────────────────────────────────────────────────

class LocationAssignedInventorySerializer(TenantModelSerializer):
    sub_location_display = serializers.CharField(source='sub_location.location_number', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = LocationAssignedInventory
        fields = TenantModelSerializer.Meta.fields + [
            'sub_location',
            'sub_location_display',
            'product',
            'product_display',
            'quantity_on_hand',
            'serial_number',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'sub_location_display',
            'product_display',
        ]


class LocationAssignedInventoryViewSet(TenantModelViewSet):
    queryset = LocationAssignedInventory.objects.all()
    serializer_class = LocationAssignedInventorySerializer
    filterset_fields = ['sub_location_id', 'product_id']
    search_fields = ['product__name', 'serial_number']
    ordering_fields = ['quantity_on_hand', 'created_on']


# ─── InventoryCount ───────────────────────────────────────────────────────────

class InventoryCountSerializer(TenantModelSerializer):
    product_display = serializers.CharField(source='product.name', read_only=True)
    counted_by_display = serializers.CharField(source='counted_by.email', read_only=True)

    class Meta:
        model = InventoryCount
        fields = TenantModelSerializer.Meta.fields + [
            'product',
            'product_display',
            'count_date',
            'counted_by',
            'counted_by_display',
            'physical_count',
            'system_count',
            'variance',
            'adjustment_applied',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_display',
            'counted_by_display',
        ]


class InventoryCountViewSet(TenantModelViewSet):
    queryset = InventoryCount.objects.all()
    serializer_class = InventoryCountSerializer
    filterset_fields = ['product_id', 'count_date', 'adjustment_applied']
    search_fields = ['product__name']
    ordering_fields = ['count_date', 'created_on']


# ─── InventoryTransfer ────────────────────────────────────────────────────────

class InventoryTransferSerializer(TenantModelSerializer):
    product_display = serializers.CharField(source='product.name', read_only=True)
    source_location_display = serializers.CharField(source='source_location.location_number', read_only=True)
    dest_location_display = serializers.CharField(source='dest_location.location_number', read_only=True)
    initiated_by_display = serializers.CharField(source='initiated_by.email', read_only=True)

    class Meta:
        model = InventoryTransfer
        fields = TenantModelSerializer.Meta.fields + [
            'product',
            'product_display',
            'source_location',
            'source_location_display',
            'dest_location',
            'dest_location_display',
            'quantity',
            'transfer_date',
            'initiated_by',
            'initiated_by_display',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_display',
            'source_location_display',
            'dest_location_display',
            'initiated_by_display',
        ]


class InventoryTransferViewSet(TenantModelViewSet):
    queryset = InventoryTransfer.objects.all()
    serializer_class = InventoryTransferSerializer
    filterset_fields = ['product_id', 'source_location_id', 'dest_location_id', 'status']
    search_fields = ['product__name']
    ordering_fields = ['transfer_date', 'created_on', 'status']


# ─── Location ─────────────────────────────────────────────────────────────────

class LocationSerializer(TenantModelSerializer):
    department_display = serializers.CharField(source='department.name', read_only=True)
    warehouse_display = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = Location
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'department',
            'department_display',
            'warehouse',
            'warehouse_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'department_display',
            'warehouse_display',
        ]


class LocationViewSet(TenantModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filterset_fields = ['department_id', 'warehouse_id']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'sub-locations', SubLocationViewSet, basename='sub-location')
router.register(r'location-assigned-inventory', LocationAssignedInventoryViewSet, basename='location-assigned-inventory')
router.register(r'inventory-counts', InventoryCountViewSet, basename='inventory-count')
router.register(r'inventory-transfers', InventoryTransferViewSet, basename='inventory-transfer')
router.register(r'locations', LocationViewSet, basename='location')
