# inventory/models.py
# Source: Data Models V6, Sections 1.3, 2.6, 3.4.
#
# Models in this app:
#   Lite tier (1.3):      InventoryItem, KitItem
#   Plus+ tier (2.6):     InvPriceHistory
#   Pro/Enterprise (3.4): Pricebook, PricebookEntry
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

import uuid
from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


# ─── Lite Tier ────────────────────────────────────────────────────────────────

class InventoryItem(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Central product/inventory catalog.
    ERD entity name: Inventory / MasterInventory.
    Django model: InventoryItem (per Data Models V6 entity mapping).
    UI label: "Product" (Lite tier), "Inventory Item" (Plus+ and above).
    Source: Data Models V6, Section 1.3.

    Stock flag fields (is_low_stock, is_out_of_stock) are system-managed.
    Do not set them manually — they are updated by background tasks when
    quantity_on_hand changes. See System Status Specification V3 Section 19.1.
    """
    numbering_entity_type = 'inventory_item'
    lifecycle_entity_type = 'inventory_item'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        HOLD = 'Hold', 'Hold'
        DISCONTINUED = 'Discontinued', 'Discontinued'

    class TypeChoices(models.TextChoices):
        SERVICE = 'Service', 'Service'
        INVENTORY = 'Product - Inventory', 'Product - Inventory'
        NON_INVENTORY = 'Product - Non-Inventory', 'Product - Non-Inventory'

    product_number = models.CharField(max_length=20, blank=True)  # Auto-generated via Numbering Service (e.g., YU-0001 for 2026)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)
    type = models.CharField(max_length=30, choices=TypeChoices.choices,
                            default=TypeChoices.SERVICE)
    category = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    taxable = models.BooleanField(default=True)
    is_bundle = models.BooleanField(default=False)
    # Plus+ — preferred vendor
    preferred_vendor = models.ForeignKey(
        'procurement.Vendor', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='preferred_products',
    )
    # Stock management — Product - Inventory type only
    low_stock_threshold = models.IntegerField(null=True, blank=True)
    # System-managed — do not set manually
    is_low_stock = models.BooleanField(default=False)
    is_out_of_stock = models.BooleanField(default=False)

    class Meta:
        db_table = 'inventory_product'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'type']),
        ]

    def __str__(self):
        return f'[{self.product_number}] {self.name}'


# Backward-compatible alias — existing code may import `Product`.
# New code should use `InventoryItem`.
Product = InventoryItem


class KitItem(TenantModel):
    """
    Items within an InventoryItem Kit (bundle).
    ERD: Kit Items (FK MasterInventory, FK Inventory).
    Source: Data Models V6, Section 1.3.
    """

    kit = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,
                            related_name='kit_items')
    product = models.ForeignKey(InventoryItem, on_delete=models.RESTRICT,
                                related_name='included_in_kits')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)

    class Meta:
        db_table = 'inventory_kititem'
        unique_together = [('tenant_id', 'kit', 'product')]

    def __str__(self):
        return f'{self.quantity}x {self.product} in kit {self.kit}'


# ─── Plus+ Tier ───────────────────────────────────────────────────────────────

class InvPriceHistory(TenantModel):
    """
    Immutable audit log of unit_cost and unit_price changes on a Product.
    ERD: InvPriceHistory (Key Inventory).
    Source: Data Models V6, Section 2.6.
    """

    product = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,
                                related_name='price_history')
    old_unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    new_unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    old_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_at = models.DateTimeField()
    changed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='price_changes')

    class Meta:
        db_table = 'inventory_invpricehistory'
        indexes = [
            models.Index(fields=['tenant_id', 'product_id']),
        ]

    def __str__(self):
        return f'{self.product} price change @ {self.changed_at}'


# ─── Pro/Enterprise Tier ──────────────────────────────────────────────────────

class Pricebook(TenantModel):
    """
    Named price list that overrides standard product prices.
    Source: Data Models V6, Section 3.4.
    """

    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_pricebook'

    def __str__(self):
        return self.name


class PricebookEntry(TenantModel, LifecycleMixin):
    """
    One product's overridden price within a Pricebook.
    Source: Data Models V6, Section 3.4.
    See System Status Specification V3 Section 23 for status transitions.
    """
    lifecycle_entity_type = 'pricebook_entry'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        DISCONTINUED = 'Discontinued', 'Discontinued'

    pricebook = models.ForeignKey(Pricebook, on_delete=models.CASCADE,
                                  related_name='entries')
    product = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,
                                related_name='pricebook_entries')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'inventory_pricebookentry'
        unique_together = [('tenant_id', 'pricebook', 'product')]

    def __str__(self):
        return f'{self.pricebook} — {self.product} @ {self.price}'
