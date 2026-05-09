# warehouse/models.py
# Source: Data Models V6, Section 2.5.
#
# Models in this app:
#   Warehouse, SubLocation, LocationAssignedInventory,
#   InventoryCount, InventoryTransfer, Location
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel


class Warehouse(TenantModel):
    """
    Physical or mobile warehouse location.
    Source: Data Models V6, Section 2.5.
    """

    class TypeChoices(models.TextChoices):
        PHYSICAL_HUB = 'Physical Hub', 'Physical Hub'
        MOBILE = 'Mobile', 'Mobile'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    warehouse_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TypeChoices.choices,
                            default=TypeChoices.PHYSICAL_HUB)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    assigned_user = models.ForeignKey('users.User', null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='assigned_warehouses')

    class Meta:
        db_table = 'warehouse_warehouse'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'[{self.warehouse_number}] {self.name}'


class SubLocation(TenantModel):
    """
    A named sub-location within a Warehouse (shelf, bin, bay, etc.).
    Source: Data Models V6, Section 2.5.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,
                                  related_name='sub_locations')
    location_number = models.CharField(max_length=20, blank=True)
    location_type = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    class Meta:
        db_table = 'warehouse_sublocation'
        indexes = [
            models.Index(fields=['tenant_id', 'warehouse_id']),
        ]

    def __str__(self):
        return f'{self.warehouse} → {self.location_number}'


class LocationAssignedInventory(TenantModel):
    """
    Quantity of a Product held at a SubLocation.
    Source: Data Models V6, Section 2.5.
    """

    sub_location = models.ForeignKey(SubLocation, on_delete=models.CASCADE,
                                     related_name='assigned_inventory')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='location_inventory')
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    serial_number = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'warehouse_locationassignedinventory'
        indexes = [
            models.Index(fields=['tenant_id', 'sub_location_id']),
            models.Index(fields=['tenant_id', 'product_id']),
        ]

    def __str__(self):
        return f'{self.product} @ {self.sub_location} ({self.quantity_on_hand})'


class InventoryCount(TenantModel):
    """
    Physical inventory count record for a Product.
    Source: Data Models V6, Section 2.5.
    """

    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='inventory_counts')
    count_date = models.DateField()
    counted_by = models.ForeignKey('users.User', null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='inventory_counts')
    physical_count = models.DecimalField(max_digits=12, decimal_places=2)
    system_count = models.DecimalField(max_digits=12, decimal_places=2)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    adjustment_applied = models.BooleanField(default=False)

    class Meta:
        db_table = 'warehouse_inventorycount'
        indexes = [
            models.Index(fields=['tenant_id', 'product_id']),
        ]

    def __str__(self):
        return f'{self.product} count @ {self.count_date}'


class InventoryTransfer(TenantModel):
    """
    Movement of inventory between two SubLocations.
    Source: Data Models V6, Section 2.5.
    """

    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'

    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='inventory_transfers')
    source_location = models.ForeignKey(SubLocation, on_delete=models.RESTRICT,
                                        related_name='transfers_out')
    dest_location = models.ForeignKey(SubLocation, on_delete=models.RESTRICT,
                                      related_name='transfers_in')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    transfer_date = models.DateField()
    initiated_by = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='initiated_transfers')
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                               default=StatusChoices.PENDING)

    class Meta:
        db_table = 'warehouse_inventorytransfer'
        indexes = [
            models.Index(fields=['tenant_id', 'product_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.product}: {self.source_location} → {self.dest_location} ({self.transfer_date})'


# ─── Organizational Locations ──────────────────────────────────────────────────

class Location(TenantModel):
    """
    Administrative or organizational location.
    Links a department or warehouse to a named physical place.
    Distinct from SubLocation, which represents a specific bin/shelf within a warehouse.
    Source: Data Models V6, Section 2.6 (Plus+).
    """

    name = models.CharField(max_length=200)
    department = models.ForeignKey('users.Department', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='locations')
    warehouse = models.ForeignKey(Warehouse, null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='locations')

    class Meta:
        db_table = 'warehouse_location'
        indexes = [
            models.Index(fields=['tenant_id', 'department_id']),
            models.Index(fields=['tenant_id', 'warehouse_id']),
        ]

    def __str__(self):
        return self.name
