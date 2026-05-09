# procurement/models.py
# Source: Data Models V6, Section 2.4.
#
# Models in this app:
#   Vendor, PurchaseOrder, PurchaseOrderLine,
#   Receiving, LotInfo, VendorBill,
#   Requisition, RequisitionLine, RMA
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from config.fields import EncryptedCharField
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Vendor(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Supplier / vendor record.
    Source: Data Models V6, Section 2.4.
    """
    numbering_entity_type = 'vendor'
    lifecycle_entity_type = 'vendor'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        DO_NOT_USE = 'Do Not Use', 'Do Not Use'  # System Status V3 §20

    vendor_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    account_number = models.CharField(max_length=50, blank=True)
    tax_id = EncryptedCharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'procurement_vendor'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'[{self.vendor_number}] {self.name}'


class VendorAccount(TenantModel):
    """Tenant's billing/credit relationship with the vendor. 1:1 with Vendor.
    Auto-created on Vendor creation via procurement.signals. Mirrors the
    Customer/Account split — billing rules describing *how the tenant does
    business with this vendor* live here, not on Vendor itself.
    Source: Data Models V6, Section 2.4."""

    class CreditStatusChoices(models.TextChoices):
        GOOD = 'Good', 'Good'
        FAIR = 'Fair', 'Fair'
        POOR = 'Poor', 'Poor'

    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE,
                                  related_name='account')
    payment_terms = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_status = models.CharField(max_length=10,
                                     choices=CreditStatusChoices.choices,
                                     default=CreditStatusChoices.GOOD)
    tax_rate = models.DecimalField(max_digits=7, decimal_places=4,
                                   null=True, blank=True)
    tax_exempt = models.BooleanField(default=False)
    pricing_tier = models.CharField(max_length=50, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    po_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'procurement_vendoraccount'
        indexes = [
            models.Index(fields=['tenant_id', 'credit_status']),
        ]

    def __str__(self):
        return f'Account for {self.vendor}'


class PurchaseOrder(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Purchase order issued to a vendor.
    Source: Data Models V6, Section 2.4.
    """
    numbering_entity_type = 'purchase_order'
    lifecycle_entity_type = 'purchase_order'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SUBMITTED = 'Submitted', 'Submitted'
        APPROVED = 'Approved', 'Approved'
        ORDERED = 'Ordered', 'Ordered'
        PARTIALLY_RECEIVED = 'Partially Received', 'Partially Received'
        RECEIVED = 'Received', 'Received'
        CANCELLED = 'Cancelled', 'Cancelled'

    po_number = models.CharField(max_length=20, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT,
                                related_name='purchase_orders')
    status = models.CharField(max_length=25, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    order_date = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    ship_to_warehouse = models.ForeignKey('warehouse.Warehouse', null=True, blank=True,
                                          on_delete=models.SET_NULL,
                                          related_name='incoming_pos')
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'procurement_purchaseorder'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'vendor_id']),
        ]

    def __str__(self):
        return f'PO {self.po_number} — {self.vendor}'


class PurchaseOrderLine(TenantModel):
    """
    Line item on a PurchaseOrder.
    Source: Data Models V6, Section 2.4.
    """

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE,
                                       related_name='lines')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='po_lines')
    quantity_ordered = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'procurement_purchaseorderline'
        indexes = [
            models.Index(fields=['tenant_id', 'purchase_order_id']),
        ]

    def __str__(self):
        return f'{self.purchase_order} — {self.product}'


class Receiving(TenantModel):
    """
    Goods receipt event against a PurchaseOrder.
    Source: Data Models V6, Section 2.4.
    """

    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.RESTRICT,
                                       related_name='receivings')
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.RESTRICT,
                                related_name='receivings')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='receivings')
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2)
    received_date = models.DateField()
    received_by = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='receivings')
    destination_location = models.ForeignKey('warehouse.SubLocation', null=True, blank=True,
                                             on_delete=models.SET_NULL,
                                             related_name='receivings')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_receiving'
        indexes = [
            models.Index(fields=['tenant_id', 'purchase_order_id']),
        ]

    def __str__(self):
        return f'Receiving {self.product} × {self.quantity_received} ({self.received_date})'


class LotInfo(TenantModel):
    """
    Lot / batch tracking for received inventory.
    Source: Data Models V6, Section 2.4.
    """

    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE,
                                  related_name='lot_info')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='lot_info')
    lot_number = models.CharField(max_length=100)
    expiration_date = models.DateField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'procurement_lotinfo'
        indexes = [
            models.Index(fields=['tenant_id', 'product_id']),
        ]

    def __str__(self):
        return f'Lot {self.lot_number} — {self.product}'


class VendorBill(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Payable bill from a vendor, typically linked to a PurchaseOrder.
    Source: Data Models V6, Section 2.4.
    """
    numbering_entity_type = 'vendor_bill'
    lifecycle_entity_type = 'vendor_bill'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        PAID = 'Paid', 'Paid'
        VOIDED = 'Voided', 'Voided'

    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT,
                                related_name='bills')
    purchase_order = models.ForeignKey(PurchaseOrder, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='bills')
    bill_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    bill_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_vendorbill'
        indexes = [
            models.Index(fields=['tenant_id', 'vendor_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'Bill {self.bill_number} — {self.vendor}'


class Requisition(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Internal purchase requisition, precursor to a PurchaseOrder.
    Source: Data Models V6, Section 2.4.
    """
    numbering_entity_type = 'requisition'
    lifecycle_entity_type = 'requisition'

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SUBMITTED = 'Submitted', 'Submitted'
        APPROVED = 'Approved', 'Approved'
        REJECTED = 'Rejected', 'Rejected'
        CONVERTED = 'Converted', 'Converted'

    requisition_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.DRAFT)
    requested_by = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='requisitions')
    approved_by = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='approved_requisitions')
    purchase_order = models.ForeignKey(PurchaseOrder, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='requisitions')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_requisition'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'Req {self.requisition_number} ({self.status})'


class RequisitionLine(TenantModel):
    """
    Line item on a Requisition.
    Source: Data Models V6, Section 2.4.
    """

    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE,
                                    related_name='lines')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='requisition_lines')
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_requisitionline'
        indexes = [
            models.Index(fields=['tenant_id', 'requisition_id']),
        ]

    def __str__(self):
        return f'{self.requisition} — {self.product}'


# ─── Returns & RMA ────────────────────────────────────────────────────────────

class RMA(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Return Merchandise Authorization for warranty/returns.
    Source: Data Models V6, Section 2.4 (Plus+).
    """
    numbering_entity_type = 'rma'
    lifecycle_entity_type = 'rma'

    class StatusChoices(models.TextChoices):
        INITIATED = 'Initiated', 'Initiated'
        SHIPPED = 'Shipped', 'Shipped'
        RECEIVED_BY_VENDOR = 'Received by Vendor', 'Received by Vendor'
        CREDITED = 'Credited', 'Credited'
        CLOSED = 'Closed', 'Closed'
        DENIED = 'Denied', 'Denied'

    class ReasonChoices(models.TextChoices):
        DEFECTIVE = 'Defective', 'Defective'
        WRONG_ITEM = 'Wrong Item', 'Wrong Item'
        DAMAGED = 'Damaged', 'Damaged'
        OVERSTOCK = 'Overstock', 'Overstock'
        OTHER = 'Other', 'Other'

    rma_number = models.CharField(max_length=20, blank=True)
    po_line = models.ForeignKey(PurchaseOrderLine, null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='rmas')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                 related_name='rmas')
    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT,
                                related_name='rmas')
    status = models.CharField(max_length=25, choices=StatusChoices.choices,
                               default=StatusChoices.INITIATED)
    reason = models.CharField(max_length=20, choices=ReasonChoices.choices,
                               default=ReasonChoices.OTHER)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    credit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'procurement_rma'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'vendor_id']),
        ]

    def __str__(self):
        return f'RMA {self.rma_number} — {self.product} ({self.status})'
