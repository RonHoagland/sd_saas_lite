# maintenance/models.py
# Source: Data Models V6, Sections 1.3, 2.2.
#
# Models in this app:
#   Asset, SubAsset, Agreement, CustomerAgreement, PreventativeMaintenance
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Asset(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A customer-owned piece of equipment tracked for maintenance.
    Source: Data Models V6, Sections 1.3, 2.2.
    """
    numbering_entity_type = 'asset'
    lifecycle_entity_type = 'asset'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        RETIRED = 'Retired', 'Retired'
        SOLD = 'Sold', 'Sold'

    asset_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='assets')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)

    # Equipment details
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    install_date = models.DateField(null=True, blank=True)
    warranty_expiration = models.DateField(null=True, blank=True)

    # Location
    address = models.ForeignKey('crm.Address', null=True, blank=True,
                                 on_delete=models.SET_NULL,
                                 related_name='assets')

    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'maintenance_asset'
        indexes = [
            models.Index(fields=['tenant_id', 'customer_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'[{self.asset_number}] {self.name}'


class SubAsset(TenantModel):
    """
    A component or sub-unit of a parent Asset.
    Source: Data Models V6, Section 2.2.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        RETIRED = 'Retired', 'Retired'

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE,
                               related_name='sub_assets')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    install_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'maintenance_subasset'
        indexes = [
            models.Index(fields=['tenant_id', 'asset_id']),
        ]

    def __str__(self):
        return f'{self.asset} → {self.name}'


class Agreement(TenantModel, NumberingMixin, LifecycleMixin):
    """
    A maintenance / service agreement template (tenant-level).
    Source: Data Models V6, Section 1.3.
    """
    numbering_entity_type = 'agreement'
    lifecycle_entity_type = 'agreement'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        ARCHIVED = 'Archived', 'Archived'

    agreement_number = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    description = models.TextField(blank=True)
    default_duration_months = models.PositiveSmallIntegerField(default=12)
    terms = models.TextField(blank=True)

    class Meta:
        db_table = 'maintenance_agreement'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return self.name


class CustomerAgreement(TenantModel):
    """
    An Agreement instance contracted with a specific Customer.
    Source: Data Models V6, Section 1.3.
    """

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        EXPIRED = 'Expired', 'Expired'
        CANCELLED = 'Cancelled', 'Cancelled'
        PENDING = 'Pending', 'Pending'

    agreement = models.ForeignKey(Agreement, on_delete=models.RESTRICT,
                                   related_name='customer_agreements')
    customer = models.ForeignKey('crm.Customer', on_delete=models.RESTRICT,
                                  related_name='agreements')
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'maintenance_customeragreement'
        indexes = [
            models.Index(fields=['tenant_id', 'customer_id']),
            models.Index(fields=['tenant_id', 'status']),
        ]

    def __str__(self):
        return f'{self.agreement} — {self.customer} ({self.start_date} → {self.end_date})'


class PreventativeMaintenance(TenantModel, NumberingMixin, LifecycleMixin):
    """
    Scheduled preventative maintenance task for an Asset.
    Source: Data Models V6, Section 2.2.
    """
    numbering_entity_type = 'preventative_maintenance'
    lifecycle_entity_type = 'preventative_maintenance'

    class FrequencyChoices(models.TextChoices):
        DAILY = 'Daily', 'Daily'
        WEEKLY = 'Weekly', 'Weekly'
        MONTHLY = 'Monthly', 'Monthly'
        QUARTERLY = 'Quarterly', 'Quarterly'
        SEMI_ANNUAL = 'Semi-Annual', 'Semi-Annual'
        ANNUAL = 'Annual', 'Annual'
        AS_NEEDED = 'As Needed', 'As Needed'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'

    pm_number = models.CharField(max_length=20, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE,
                               related_name='pm_schedules')
    task_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=15, choices=FrequencyChoices.choices,
                                  default=FrequencyChoices.MONTHLY)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                               default=StatusChoices.ACTIVE)
    last_performed_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name='pm_tasks')
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2,
                                           null=True, blank=True)

    class Meta:
        db_table = 'maintenance_preventativemaintenance'
        indexes = [
            models.Index(fields=['tenant_id', 'asset_id']),
            models.Index(fields=['tenant_id', 'next_due_date']),
        ]

    def __str__(self):
        return f'{self.asset} — {self.task_name} ({self.frequency})'
