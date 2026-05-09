# inventory/api.py
# REST API serializers and viewsets for inventory app models.
#
# Models:
#   InventoryItem, KitItem, InvPriceHistory, Pricebook, PricebookEntry

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet, ReadOnlyTenantViewSet
from .models import (
    InventoryItem, KitItem, InvPriceHistory, Pricebook, PricebookEntry
)


# ─── InventoryItem ────────────────────────────────────────────────────────────

class InventoryItemSerializer(TenantModelSerializer):
    preferred_vendor_display = serializers.CharField(source='preferred_vendor.name', read_only=True)

    class Meta:
        model = InventoryItem
        fields = TenantModelSerializer.Meta.fields + [
            'product_number',
            'name',
            'status',
            'type',
            'category',
            'sku',
            'unit_cost',
            'unit_price',
            'description',
            'taxable',
            'is_bundle',
            'preferred_vendor',
            'preferred_vendor_display',
            'low_stock_threshold',
            'is_low_stock',
            'is_out_of_stock',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_number',
            'preferred_vendor_display',
            'is_low_stock',
            'is_out_of_stock',
        ]


class InventoryItemViewSet(TenantModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    filterset_fields = ['status', 'type', 'preferred_vendor_id', 'is_bundle']
    search_fields = ['name', 'product_number', 'sku', 'category']
    ordering_fields = ['name', 'product_number', 'created_on', 'status']


# ─── KitItem ──────────────────────────────────────────────────────────────────

class KitItemSerializer(TenantModelSerializer):
    kit_display = serializers.CharField(source='kit.name', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = KitItem
        fields = TenantModelSerializer.Meta.fields + [
            'kit',
            'kit_display',
            'product',
            'product_display',
            'quantity',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'kit_display',
            'product_display',
        ]


class KitItemViewSet(TenantModelViewSet):
    queryset = KitItem.objects.all()
    serializer_class = KitItemSerializer
    filterset_fields = ['kit_id', 'product_id']
    search_fields = ['kit__name', 'product__name']
    ordering_fields = ['created_on']


# ─── InvPriceHistory ──────────────────────────────────────────────────────────

class InvPriceHistorySerializer(TenantModelSerializer):
    product_display = serializers.CharField(source='product.name', read_only=True)
    changed_by_display = serializers.CharField(source='changed_by.email', read_only=True)

    class Meta:
        model = InvPriceHistory
        fields = TenantModelSerializer.Meta.fields + [
            'product',
            'product_display',
            'old_unit_cost',
            'new_unit_cost',
            'old_unit_price',
            'new_unit_price',
            'changed_at',
            'changed_by',
            'changed_by_display',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'product_display',
            'changed_by_display',
        ]


class InvPriceHistoryViewSet(ReadOnlyTenantViewSet):
    queryset = InvPriceHistory.objects.all()
    serializer_class = InvPriceHistorySerializer
    filterset_fields = ['product_id', 'changed_by_id']
    search_fields = ['product__name']
    ordering_fields = ['changed_at', 'created_on']


# ─── Pricebook ────────────────────────────────────────────────────────────────

class PricebookSerializer(TenantModelSerializer):

    class Meta:
        model = Pricebook
        fields = TenantModelSerializer.Meta.fields + [
            'name',
            'is_active',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class PricebookViewSet(TenantModelViewSet):
    queryset = Pricebook.objects.all()
    serializer_class = PricebookSerializer
    filterset_fields = ['is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'created_on']


# ─── PricebookEntry ───────────────────────────────────────────────────────────

class PricebookEntrySerializer(TenantModelSerializer):
    pricebook_display = serializers.CharField(source='pricebook.name', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PricebookEntry
        fields = TenantModelSerializer.Meta.fields + [
            'pricebook',
            'pricebook_display',
            'product',
            'product_display',
            'price',
            'status',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'pricebook_display',
            'product_display',
        ]


class PricebookEntryViewSet(TenantModelViewSet):
    queryset = PricebookEntry.objects.all()
    serializer_class = PricebookEntrySerializer
    filterset_fields = ['pricebook_id', 'product_id', 'status']
    search_fields = ['pricebook__name', 'product__name']
    ordering_fields = ['price', 'created_on', 'status']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'inventory-items', InventoryItemViewSet, basename='inventory-item')
router.register(r'kit-items', KitItemViewSet, basename='kit-item')
router.register(r'inv-price-history', InvPriceHistoryViewSet, basename='inv-price-history')
router.register(r'pricebooks', PricebookViewSet, basename='pricebook')
router.register(r'pricebook-entries', PricebookEntryViewSet, basename='pricebook-entry')
