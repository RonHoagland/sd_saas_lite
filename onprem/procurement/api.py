# procurement/api.py
# REST API serializers and viewsets for procurement app models.
#
# Models:
#   Vendor, PurchaseOrder, PurchaseOrderLine, Receiving, LotInfo,
#   VendorBill, Requisition, RequisitionLine, RMA

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import TenantModelSerializer, TenantModelViewSet, TenantNoDeleteViewSet
from .models import (
    Vendor, PurchaseOrder, PurchaseOrderLine, Receiving, LotInfo,
    VendorBill, Requisition, RequisitionLine, RMA
)


# ─── Vendor ───────────────────────────────────────────────────────────────────

class VendorSerializer(TenantModelSerializer):

    class Meta:
        model = Vendor
        fields = TenantModelSerializer.Meta.fields + [
            'vendor_number',
            'name',
            'status',
            'account_number',
            'payment_terms',
            'tax_id',
            'notes',
            'tags',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'vendor_number',
        ]


class VendorViewSet(TenantModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filterset_fields = ['status']
    search_fields = ['name', 'vendor_number', 'account_number']
    ordering_fields = ['name', 'created_on', 'status']


# ─── PurchaseOrder ────────────────────────────────────────────────────────────

class PurchaseOrderSerializer(TenantModelSerializer):
    vendor_display = serializers.CharField(source='vendor.name', read_only=True)
    warehouse_display = serializers.CharField(source='ship_to_warehouse.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = TenantModelSerializer.Meta.fields + [
            'po_number',
            'vendor',
            'vendor_display',
            'status',
            'order_date',
            'expected_date',
            'ship_to_warehouse',
            'warehouse_display',
            'notes',
            'subtotal',
            'tax_amount',
            'total',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'po_number',
            'vendor_display',
            'warehouse_display',
        ]


class PurchaseOrderViewSet(TenantModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['vendor_id', 'status', 'ship_to_warehouse_id']
    search_fields = ['po_number', 'vendor__name']
    ordering_fields = ['order_date', 'expected_date', 'created_on', 'status']


# ─── PurchaseOrderLine ────────────────────────────────────────────────────────

class PurchaseOrderLineSerializer(TenantModelSerializer):
    purchase_order_display = serializers.CharField(source='purchase_order.po_number', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = TenantModelSerializer.Meta.fields + [
            'purchase_order',
            'purchase_order_display',
            'product',
            'product_display',
            'quantity_ordered',
            'quantity_received',
            'unit_cost',
            'line_total',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'purchase_order_display',
            'product_display',
        ]


class PurchaseOrderLineViewSet(TenantModelViewSet):
    queryset = PurchaseOrderLine.objects.all()
    serializer_class = PurchaseOrderLineSerializer
    filterset_fields = ['purchase_order_id', 'product_id']
    search_fields = ['product__name']
    ordering_fields = ['created_on']


# ─── Receiving ────────────────────────────────────────────────────────────────

class ReceivingSerializer(TenantModelSerializer):
    purchase_order_display = serializers.CharField(source='purchase_order.po_number', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)
    received_by_display = serializers.CharField(source='received_by.email', read_only=True)
    location_display = serializers.CharField(source='destination_location.location_number', read_only=True)

    class Meta:
        model = Receiving
        fields = TenantModelSerializer.Meta.fields + [
            'purchase_order',
            'purchase_order_display',
            'po_line',
            'product',
            'product_display',
            'quantity_received',
            'received_date',
            'received_by',
            'received_by_display',
            'destination_location',
            'location_display',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'purchase_order_display',
            'product_display',
            'received_by_display',
            'location_display',
        ]


class ReceivingViewSet(TenantModelViewSet):
    queryset = Receiving.objects.all()
    serializer_class = ReceivingSerializer
    filterset_fields = ['purchase_order_id', 'product_id', 'received_date']
    search_fields = ['product__name', 'purchase_order__po_number']
    ordering_fields = ['received_date', 'created_on']


# ─── LotInfo ──────────────────────────────────────────────────────────────────

class LotInfoSerializer(TenantModelSerializer):
    receiving_display = serializers.SerializerMethodField(read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    def get_receiving_display(self, obj):
        return f"Receiving {obj.receiving_id}"

    class Meta:
        model = LotInfo
        fields = TenantModelSerializer.Meta.fields + [
            'receiving',
            'receiving_display',
            'product',
            'product_display',
            'lot_number',
            'expiration_date',
            'quantity',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'receiving_display',
            'product_display',
        ]


class LotInfoViewSet(TenantModelViewSet):
    queryset = LotInfo.objects.all()
    serializer_class = LotInfoSerializer
    filterset_fields = ['product_id', 'receiving_id']
    search_fields = ['lot_number', 'product__name']
    ordering_fields = ['expiration_date', 'created_on']


# ─── VendorBill ───────────────────────────────────────────────────────────────

class VendorBillSerializer(TenantModelSerializer):
    vendor_display = serializers.CharField(source='vendor.name', read_only=True)
    purchase_order_display = serializers.CharField(source='purchase_order.po_number', read_only=True)

    class Meta:
        model = VendorBill
        fields = TenantModelSerializer.Meta.fields + [
            'vendor',
            'vendor_display',
            'purchase_order',
            'purchase_order_display',
            'bill_number',
            'status',
            'bill_date',
            'due_date',
            'subtotal',
            'tax_amount',
            'total',
            'amount_paid',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'bill_number',
            'vendor_display',
            'purchase_order_display',
        ]


class VendorBillViewSet(TenantModelViewSet):
    queryset = VendorBill.objects.all()
    serializer_class = VendorBillSerializer
    filterset_fields = ['vendor_id', 'status']
    search_fields = ['bill_number', 'vendor__name']
    ordering_fields = ['bill_date', 'due_date', 'created_on', 'status']


# ─── Requisition ──────────────────────────────────────────────────────────────

class RequisitionSerializer(TenantModelSerializer):
    requested_by_display = serializers.CharField(source='requested_by.email', read_only=True)
    approved_by_display = serializers.CharField(source='approved_by.email', read_only=True)
    purchase_order_display = serializers.CharField(source='purchase_order.po_number', read_only=True)

    class Meta:
        model = Requisition
        fields = TenantModelSerializer.Meta.fields + [
            'requisition_number',
            'status',
            'requested_by',
            'requested_by_display',
            'approved_by',
            'approved_by_display',
            'purchase_order',
            'purchase_order_display',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'requisition_number',
            'requested_by_display',
            'approved_by_display',
            'purchase_order_display',
        ]


class RequisitionViewSet(TenantModelViewSet):
    queryset = Requisition.objects.all()
    serializer_class = RequisitionSerializer
    filterset_fields = ['status']
    search_fields = ['requisition_number']
    ordering_fields = ['created_on', 'status']


# ─── RequisitionLine ──────────────────────────────────────────────────────────

class RequisitionLineSerializer(TenantModelSerializer):
    requisition_display = serializers.CharField(source='requisition.requisition_number', read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = RequisitionLine
        fields = TenantModelSerializer.Meta.fields + [
            'requisition',
            'requisition_display',
            'product',
            'product_display',
            'quantity_requested',
            'estimated_unit_cost',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'requisition_display',
            'product_display',
        ]


class RequisitionLineViewSet(TenantModelViewSet):
    queryset = RequisitionLine.objects.all()
    serializer_class = RequisitionLineSerializer
    filterset_fields = ['requisition_id', 'product_id']
    search_fields = ['product__name']
    ordering_fields = ['created_on']


# ─── RMA ──────────────────────────────────────────────────────────────────────

class RMASerializer(TenantModelSerializer):
    po_line_display = serializers.SerializerMethodField(read_only=True)
    product_display = serializers.CharField(source='product.name', read_only=True)
    vendor_display = serializers.CharField(source='vendor.name', read_only=True)

    def get_po_line_display(self, obj):
        return f"PO Line {obj.po_line_id}" if obj.po_line else None

    class Meta:
        model = RMA
        fields = TenantModelSerializer.Meta.fields + [
            'rma_number',
            'po_line',
            'po_line_display',
            'product',
            'product_display',
            'vendor',
            'vendor_display',
            'status',
            'reason',
            'quantity',
            'credit_amount',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'rma_number',
            'po_line_display',
            'product_display',
            'vendor_display',
        ]


class RMAViewSet(TenantModelViewSet):
    queryset = RMA.objects.all()
    serializer_class = RMASerializer
    filterset_fields = ['vendor_id', 'product_id', 'status', 'reason']
    search_fields = ['rma_number', 'product__name', 'vendor__name']
    ordering_fields = ['created_on', 'status']


# ─── Router ───────────────────────────────────────────────────────────────────

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-lines', PurchaseOrderLineViewSet, basename='purchase-order-line')
router.register(r'receivings', ReceivingViewSet, basename='receiving')
router.register(r'lot-info', LotInfoViewSet, basename='lot-info')
router.register(r'vendor-bills', VendorBillViewSet, basename='vendor-bill')
router.register(r'requisitions', RequisitionViewSet, basename='requisition')
router.register(r'requisition-lines', RequisitionLineViewSet, basename='requisition-line')
router.register(r'rmas', RMAViewSet, basename='rma')
