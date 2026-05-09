# procurement/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from procurement.models import (
    Vendor, VendorAccount, PurchaseOrder, PurchaseOrderLine,
    Receiving, LotInfo, VendorBill,
    Requisition, RequisitionLine, RMA,
)


@admin.register(Vendor)
class VendorAdmin(TenantModelAdmin):
    list_display = ('vendor_number', 'name', 'status', 'account_number', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('vendor_number', 'name', 'account_number')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(VendorAccount)
class VendorAccountAdmin(TenantModelAdmin):
    list_display = ('vendor', 'payment_terms', 'credit_limit', 'credit_status',
                    'pricing_tier', 'discount_percentage', 'po_required',
                    'tax_exempt', 'tenant_id')
    list_filter = ('tenant_id', 'credit_status', 'tax_exempt', 'po_required')
    search_fields = ('vendor__vendor_number', 'vendor__name',
                     'vendor__account_number')
    raw_id_fields = ('vendor',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(TenantModelAdmin):
    list_display = ('po_number', 'vendor', 'status', 'order_date',
                    'expected_date', 'total', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('po_number', 'vendor__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(TenantModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity_ordered',
                    'quantity_received', 'unit_cost', 'line_total', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('purchase_order__po_number', 'product__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Receiving)
class ReceivingAdmin(TenantModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity_received',
                    'received_date', 'received_by', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('purchase_order__po_number', 'product__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(LotInfo)
class LotInfoAdmin(TenantModelAdmin):
    list_display = ('lot_number', 'product', 'quantity', 'expiration_date', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('lot_number', 'product__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(VendorBill)
class VendorBillAdmin(TenantModelAdmin):
    list_display = ('bill_number', 'vendor', 'status', 'bill_date',
                    'due_date', 'total', 'amount_paid', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('bill_number', 'vendor__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(Requisition)
class RequisitionAdmin(TenantModelAdmin):
    list_display = ('requisition_number', 'status', 'requested_by',
                    'approved_by', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('requisition_number',)
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(RequisitionLine)
class RequisitionLineAdmin(TenantModelAdmin):
    list_display = ('requisition', 'product', 'quantity_requested',
                    'estimated_unit_cost', 'tenant_id')
    list_filter = ('tenant_id',)
    search_fields = ('requisition__requisition_number', 'product__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')


@admin.register(RMA)
class RMAAdmin(TenantModelAdmin):
    list_display = ('rma_number', 'product', 'vendor', 'status', 'reason', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'reason')
    search_fields = ('rma_number', 'product__name', 'vendor__name')
    readonly_fields = ('id', 'tenant_id', 'created_on', 'updated_on')
