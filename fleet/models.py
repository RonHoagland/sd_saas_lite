# fleet/models.py
# Source: Data Models V6, Section 4.
#
# Models in this app:
#   Vehicle, VehicleMaintenance, MileageLog, VehicleInventory
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Vehicle(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A company-owned or leased vehicle in the tenant's fleet.
    Source: Data Models V6, Section 4.
    """
    numbering_entity_type = 'vehicle'
    lifecycle_entity_type = 'vehicle'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        IN_SERVICE = 'In Service', 'In Service'
        OUT_OF_SERVICE = 'Out of Service', 'Out of Service'
        RETIRED = 'Retired', 'Retired'

    class TypeChoices(models.TextChoices):
        VAN = 'Van', 'Van'
        TRUCK = 'Truck', 'Truck'
        CAR = 'Car', 'Car'
        TRAILER = 'Trailer', 'Trailer'
        HEAVY_EQUIPMENT = 'Heavy Equipment', 'Heavy Equipment'
        OTHER = 'Other', 'Other'

    vehicle_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    vehicle_type = models.CharField(max_length=20, choices=TypeChoices.choices,
                                     default=TypeChoices.VAN)
    status = models.CharField(max_length=15, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    vin = models.CharField(max_length=17, blank=True, verbose_name='VIN')
    license_plate = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=50, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='assigned_vehicles')
    assigned_work_group = models.ForeignKey('workforce.WorkGroup', null=True, blank=True,
                                             on_delete=models.SET_NULL,
                                             related_name='vehicles')
    registration_expiry = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'fleet_vehicle'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'[{self.vehicle_number}] {self.year} {self.make} {self.model}'


class VehicleMaintenance(TenantModel, LifecycleMixin):
    """
    A maintenance record (service event) for a Vehicle.
    Source: Data Models V6, Section 4.
    """
    lifecycle_entity_type = 'vehicle_maintenance'

    class StatusChoices(models.TextChoices):
        SCHEDULED = 'Scheduled', 'Scheduled'
        COMPLETED = 'Completed', 'Completed'
        OVERDUE = 'Overdue', 'Overdue'
        CANCELLED = 'Cancelled', 'Cancelled'

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE,
                                 related_name='maintenance_records')
    service_type = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.SCHEDULED)
    service_date = models.DateField(null=True, blank=True)
    next_service_date = models.DateField(null=True, blank=True)
    mileage_at_service = models.PositiveIntegerField(null=True, blank=True)
    next_service_mileage = models.PositiveIntegerField(null=True, blank=True)
    performed_by = models.CharField(max_length=200, blank=True,
                                     help_text='Vendor name or internal user description.')
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'fleet_vehiclemaintenance'
        indexes = [
            models.Index(fields=['tenant_id', 'vehicle_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.vehicle} — {self.service_type} ({self.service_date})'


class MileageLog(TenantModel):
    """
    Mileage / odometer log entry for a Vehicle.
    Source: Data Models V6, Section 4.
    """

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE,
                                 related_name='mileage_logs')
    log_date = models.DateField()
    odometer_start = models.PositiveIntegerField(default=0)
    odometer_end = models.PositiveIntegerField(default=0)
    miles_driven = models.PositiveIntegerField(default=0)
    driver = models.ForeignKey('users.User', null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='mileage_logs')
    purpose = models.CharField(max_length=300, blank=True)
    notes = models.TextField(blank=True)

    # Optional work order link
    work_order = models.ForeignKey('service.WorkOrder', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='mileage_logs')

    class Meta:
        db_table = 'fleet_mileagelog'
        indexes = [
            models.Index(fields=['tenant_id', 'vehicle_id']),
            models.Index(fields=['tenant_id', 'log_date']),
        ]

    def __str__(self):
        return f'{self.vehicle} — {self.miles_driven} mi ({self.log_date})'


class VehicleInventory(TenantModel):
    """
    Inventory / parts stocked in a Vehicle (mobile warehouse).
    Source: Data Models V6, Section 4.
    """

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE,
                                 related_name='vehicle_inventory')
    product = models.ForeignKey('inventory.InventoryItem', on_delete=models.RESTRICT,
                                related_name='vehicle_inventory')
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'fleet_vehicleinventory'
        indexes = [
            models.Index(fields=['tenant_id', 'vehicle_id']),
            models.Index(fields=['tenant_id', 'product_id']),
        ]

    def __str__(self):
        return f'{self.vehicle} — {self.product} ({self.quantity_on_hand})'
